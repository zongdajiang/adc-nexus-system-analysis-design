package cn.adcnexus;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import java.util.regex.*;

/** Parameterized JDBC access. No ORM. The lock is held by the database, not by a JVM. */
public final class Db {
  private static final Map<String, Set<String>> TABLE_COLUMNS =
      new java.util.concurrent.ConcurrentHashMap<>();
  public final boolean postgres;
  private final String url;
  private final Properties properties = new Properties();
  private final HikariDataSource pool;
  private final java.util.concurrent.Semaphore connections =
      new java.util.concurrent.Semaphore(12, true);

  public Db() throws Exception {
    String source = System.getenv("DATABASE_URL");
    postgres = source != null && !source.isBlank();
    if (postgres) {
      Support.check(
          source.startsWith("jdbc:postgresql://")
              || source.startsWith("postgresql://")
              || source.startsWith("postgres://"),
          500,
          "DATABASE_CONFIG",
          "DATABASE_URL 必须为 PostgreSQL 连接串");
      if (source.startsWith("jdbc:")) url = source;
      else {
        java.net.URI uri = java.net.URI.create(source);
        String[] user = uri.getRawUserInfo().split(":", 2);
        properties.setProperty("user", java.net.URLDecoder.decode(user[0], StandardCharsets.UTF_8));
        properties.setProperty(
            "password", java.net.URLDecoder.decode(user[1], StandardCharsets.UTF_8));
        url =
            "jdbc:postgresql://"
                + uri.getHost()
                + ":"
                + (uri.getPort() < 0 ? 5432 : uri.getPort())
                + uri.getPath()
                + "?"
                + (uri.getRawQuery() == null ? "sslmode=require" : uri.getRawQuery());
      }
      properties.setProperty("connectTimeout", "15");
      properties.setProperty("socketTimeout", "30");
      properties.setProperty("tcpKeepAlive", "true");
    } else {
      Path data = Path.of(System.getenv().getOrDefault("DATA_DIR", "data")).toAbsolutePath();
      Files.createDirectories(data);
      url = "jdbc:sqlite:" + data.resolve("adc-nexus.sqlite");
    }
    if (postgres) {
      HikariConfig config = new HikariConfig();
      config.setJdbcUrl(url);
      config.setDataSourceProperties(properties);
      config.setPoolName("adc-jdbc");
      config.setMaximumPoolSize(8);
      config.setMinimumIdle(0);
      config.setConnectionTimeout(8000);
      config.setValidationTimeout(4000);
      config.setIdleTimeout(30000);
      config.setMaxLifetime(900000);
      config.setKeepaliveTime(0);
      config.setInitializationFailTimeout(-1);
      pool = new HikariDataSource(config);
    } else pool = null;
  }

  public Connection open() throws SQLException {
    Connection c = postgres ? pool.getConnection() : DriverManager.getConnection(url, properties);
    if (!postgres) {
      try (Statement s = c.createStatement()) {
        s.execute("PRAGMA foreign_keys=ON");
        s.execute("PRAGMA busy_timeout=15000");
      }
    }
    return c;
  }

  public void close() {
    if (pool != null) pool.close();
  }

  @FunctionalInterface
  public interface Work<T> {
    T run(Connection c) throws Exception;
  }

  private void acquire() throws InterruptedException {
    Support.check(
        connections.tryAcquire(8, java.util.concurrent.TimeUnit.SECONDS),
        503,
        "BUSY",
        "当前请求较多，请稍后重试");
  }

  public <T> T read(Work<T> w) throws Exception {
    acquire();
    try (Connection c = open()) {
      return w.run(c);
    } finally {
      connections.release();
    }
  }

  public <T> T tx(Work<T> w) throws Exception {
    acquire();
    try (Connection c = open()) {
      if (postgres) {
        c.setAutoCommit(false);
        execute(c, "SELECT pg_advisory_xact_lock(810224025)");
      } else {
        try (Statement s = c.createStatement()) {
          s.execute("BEGIN IMMEDIATE");
        }
      }
      try {
        T r = w.run(c);
        if (postgres) c.commit();
        else execute(c, "COMMIT");
        return r;
      } catch (Exception e) {
        try {
          if (postgres) c.rollback();
          else execute(c, "ROLLBACK");
        } catch (Exception suppressed) {
          e.addSuppressed(suppressed);
        }
        throw e;
      }
    } finally {
      connections.release();
    }
  }

  public static List<Map<String, Object>> rows(Connection c, String sql, Object... args)
      throws SQLException {
    try (PreparedStatement p = bind(c, sql, args);
        ResultSet r = p.executeQuery()) {
      List<Map<String, Object>> out = new ArrayList<>();
      ResultSetMetaData m = r.getMetaData();
      while (r.next()) {
        Map<String, Object> row = new LinkedHashMap<>();
        for (int i = 1; i <= m.getColumnCount(); i++) row.put(m.getColumnLabel(i), r.getObject(i));
        out.add(row);
      }
      return out;
    }
  }

  public static Map<String, Object> one(Connection c, String sql, Object... args)
      throws SQLException {
    var rows = rows(c, sql, args);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  public static long count(Connection c, String sql, Object... args) throws SQLException {
    var row = one(c, sql, args);
    return row == null ? 0 : ((Number) row.values().iterator().next()).longValue();
  }

  public static int execute(Connection c, String sql, Object... args) throws SQLException {
    try (PreparedStatement p = bind(c, sql, args)) {
      if (p.execute()) return 0;
      return p.getUpdateCount();
    }
  }

  private static PreparedStatement bind(Connection c, String sql, Object... args)
      throws SQLException {
    PreparedStatement p = c.prepareStatement(sql);
    for (int i = 0; i < args.length; i++) p.setObject(i + 1, args[i]);
    return p;
  }

  public static void insert(Connection c, String table, Map<String, Object> row)
      throws SQLException {
    identifier(table);
    row.keySet().forEach(Db::identifier);
    Set<String> columns = TABLE_COLUMNS.get(table);
    if (columns == null) {
      columns = new HashSet<>();
      try (ResultSet rs = c.getMetaData().getColumns(null, null, table, null)) {
        while (rs.next()) columns.add(rs.getString("COLUMN_NAME"));
      }
      TABLE_COLUMNS.put(table, Set.copyOf(columns));
    }
    row = new LinkedHashMap<>(row);
    for (String timestamp : List.of("created_at", "updated_at"))
      if (columns.contains(timestamp) && !row.containsKey(timestamp))
        row.put(timestamp, Support.now());
    execute(
        c,
        "INSERT INTO "
            + table
            + " ("
            + String.join(",", row.keySet())
            + ") VALUES ("
            + String.join(",", Collections.nCopies(row.size(), "?"))
            + ")",
        row.values().toArray());
  }

  public static void update(Connection c, String table, String id, Map<String, Object> values)
      throws SQLException {
    identifier(table);
    values.keySet().forEach(Db::identifier);
    List<Object> a = new ArrayList<>(values.values());
    a.add(id);
    execute(
        c,
        "UPDATE "
            + table
            + " SET "
            + String.join(",", values.keySet().stream().map(k -> k + "=?").toList())
            + " WHERE id=?",
        a.toArray());
  }

  private static void identifier(String s) {
    if (!s.matches("[a-z_]+")) throw new IllegalArgumentException("Invalid SQL identifier");
  }

  public static String resource(String path) throws Exception {
    try (var in = Db.class.getResourceAsStream(path)) {
      if (in == null) throw new IllegalStateException("Missing resource " + path);
      return new String(in.readAllBytes(), StandardCharsets.UTF_8);
    }
  }

  public static List<String> splitSql(String sql) {
    List<String> out = new ArrayList<>();
    StringBuilder b = new StringBuilder();
    boolean quoted = false, comment = false;
    for (int i = 0; i < sql.length(); i++) {
      char ch = sql.charAt(i);
      if (comment) {
        if (ch == '\n') comment = false;
        else continue;
      }
      if (!quoted && ch == '-' && i + 1 < sql.length() && sql.charAt(i + 1) == '-') {
        comment = true;
        i++;
        continue;
      }
      if (ch == '\'') {
        if (quoted && i + 1 < sql.length() && sql.charAt(i + 1) == '\'') {
          b.append("''");
          i++;
          continue;
        }
        quoted = !quoted;
      }
      if (ch == ';' && !quoted) {
        if (!b.toString().isBlank()) out.add(b.toString().trim());
        b.setLength(0);
      } else b.append(ch);
    }
    if (!b.toString().isBlank()) out.add(b.toString().trim());
    return out;
  }

  private void script(Connection c, String resource) throws Exception {
    // Only version-controlled schema/fixtures reach this method. User values
    // always go through PreparedStatement. Batching avoids startup RTT costs.
    try (Statement batch = c.createStatement()) {
      for (String s : splitSql(resource(resource))) if (!s.startsWith("PRAGMA")) batch.addBatch(s);
      batch.executeBatch();
    }
  }

  public void migrate() throws Exception {
    if (!postgres)
      read(
          c -> {
            execute(c, "PRAGMA journal_mode=WAL");
            return null;
          });
    tx(
        c -> {
          execute(
              c,
              "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at"
                  + " TEXT NOT NULL)");
          if (count(c, "SELECT COUNT(*) FROM schema_migrations WHERE version='001'") == 0) {
            script(c, "/db/baseline-" + (postgres ? "postgres" : "sqlite") + ".sql");
            script(c, "/db/extensions.sql");
            execute(
                c,
                "INSERT INTO schema_migrations(version,applied_at) VALUES ('001',?)",
                Support.now());
          }
          if (Boolean.parseBoolean(System.getenv().getOrDefault("SEED_DATA", "true"))
              && count(c, "SELECT COUNT(*) FROM organizations") == 0) {
            script(c, "/db/seed" + (postgres ? "-postgres" : "") + ".sql");
            Seed.complete(c, this);
          }
          if (count(c, "SELECT COUNT(*) FROM schema_migrations WHERE version='002'") == 0) {
            Seed.normalizeLegacyStates(c);
            execute(
                c,
                "INSERT INTO schema_migrations(version,applied_at) VALUES ('002',?)",
                Support.now());
          }
          if (count(c, "SELECT COUNT(*) FROM schema_migrations WHERE version='003'") == 0) {
            execute(
                c,
                "DELETE FROM role_permissions WHERE role_id IN"
                    + " ('jdbc-role-FRONT_DESK','jdbc-role-CASHIER') AND permission_id IN (SELECT"
                    + " id FROM permissions WHERE code='clinical.read')");
            execute(
                c,
                "INSERT INTO schema_migrations(version,applied_at) VALUES ('003',?)",
                Support.now());
          }
          if (count(c, "SELECT COUNT(*) FROM schema_migrations WHERE version='004'") == 0) {
            execute(
                c,
                "CREATE TABLE IF NOT EXISTS clinical_note_signatures (id TEXT PRIMARY KEY,"
                    + " note_version_id TEXT NOT NULL UNIQUE REFERENCES clinical_note_versions(id),"
                    + " dentist_id TEXT NOT NULL REFERENCES dentists(id), signer_user_id TEXT NOT"
                    + " NULL REFERENCES app_users(id), content_checksum TEXT NOT NULL, signed_at"
                    + " TEXT NOT NULL)");
            execute(
                c,
                "INSERT INTO schema_migrations(version,applied_at) VALUES ('004',?)",
                Support.now());
          }
          return null;
        });
  }
}
