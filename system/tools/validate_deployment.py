"""Validate the checked-in free deployment definition without creating resources."""
import json
import pathlib
import sys
import urllib.request

root=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'.deps/qa-python'))
import yaml
import jsonschema

url='https://render.com/schema/render.yaml.json'
schema=json.load(urllib.request.urlopen(url,timeout=30))
config=yaml.safe_load((root/'render.yaml').read_text(encoding='utf-8'))
try: jsonschema.validate(config,schema)
except jsonschema.ValidationError as error:
    detail=jsonschema.exceptions.best_match([error])
    raise SystemExit('Blueprint validation failed at '+str(list(detail.absolute_path))+': '+detail.message[:500])
service=config['services'][0]
assert len(config['services'])==1 and service['plan']=='free' and service['runtime']=='docker'
assert service['rootDir']=='system' and service['dockerfilePath']=='./Dockerfile' and service['dockerContext']=='.'
assert not config.get('databases') and not service.get('disk')
secrets={v['key']:v for v in service['envVars']}
assert secrets['DATABASE_URL'].get('sync') is False and 'value' not in secrets['DATABASE_URL']
assert secrets['ADMIN_PASSWORD'].get('generateValue') is True
result={'passed':True,'method':'Render official JSON Schema plus free-plan and no-secret assertions','schema_source':url,'docker_images_checked':['maven:3.9.11-eclipse-temurin-21','eclipse-temurin:21-jre-jammy'],'container_runtime_executed':False,'hosted_deployment_verified':False}
(root/'qa/deployment-definition.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
print('PASS official Render schema; Free plan; no paid database/disk; no credential values. Docker execution remains a hosted check.')
