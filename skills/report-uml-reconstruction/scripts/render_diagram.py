#!/usr/bin/env python3
"""Data-driven report diagram renderer. Python 3.10+, Pillow; no network calls.

JSON model -> SVG, PNG, uncompressed editable draw.io, scene and layout audit.
Coordinates are logical pixels. New diagrams use measured text-aware layouts;
source reconstructions may use explicit coordinates. All outputs derive from one scene.
"""
from __future__ import annotations
import argparse, json, math, os, re, sys
from pathlib import Path
from html import escape
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageColor

PROFILES={
 'mayuyang': {'font':'Microsoft YaHei','latin':'Arial','size':12,'stroke':'#000000','line':1,'fill':'#ffffff','shadow':False,'activation':'#ffffff'},
 'b-enterprise': {'font':'SimSun','latin':'Arial','size':14,'stroke':'#111111','line':1,'fill':'#fceee3','shadow':True,'activation':'#ffffff'},
}
FONT_OVERRIDE=None
def font_path(family='SimSun',bold=False):
    if FONT_OVERRIDE: return FONT_OVERRIDE
    win=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    options=([win/('arialbd.ttf' if bold else 'arial.ttf')] if family=='Arial' else [win/'msyh.ttc',win/'simhei.ttf'] if family=='Microsoft YaHei' else [win/'simsun.ttc',win/'msyh.ttc',win/'simhei.ttf'])
    options += [Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'),Path('/System/Library/Fonts/PingFang.ttc')]
    for p in options:
        if p.is_file():return str(p)
    raise RuntimeError('未找到中文字体。请安装 Noto Sans CJK 或用 --font 指定中文 .ttf/.ttc 文件。')
_FC={}
def get_font(size,family='SimSun',bold=False,scale=1):
    key=(size,family,bold,scale,FONT_OVERRIDE)
    if key not in _FC: _FC[key]=ImageFont.truetype(font_path(family,bold),max(1,round(size*scale)))
    return _FC[key]
def measure(s,size,family='SimSun',bold=False):
    f=get_font(size,family,bold); b=f.getbbox(str(s),anchor='ls')
    return f.getlength(str(s)),b[3]-b[1]
def label_family(s,default='SimSun'):
    return default if re.search(r'[\u4e00-\u9fff]',str(s)) else 'Arial'
def wrap(s,width,size,family='SimSun',bold=False):
    """Preserve explicit newlines. Break CJK at glyphs, prefer spaces in Latin labels."""
    result=[]
    for paragraph in str(s).split('\n'):
        if measure(paragraph,size,family,bold)[0]<=width:result.append(paragraph);continue
        line=''
        for c in paragraph:
            if line and measure(line+c,size,family,bold)[0]>width:
                if ' ' in line and not re.search(r'[\u4e00-\u9fff]',line):
                    a,b=line.rsplit(' ',1); result.append(a);line=b+c
                else:result.append(line);line=c
            else:line+=c
        result.append(line)
    return '\n'.join(result)
def port(cx,cy,rx,ry,tx,ty):
    dx,dy=tx-cx,ty-cy
    if not dx and not dy:return cx,cy
    k=1/math.sqrt((dx/rx)**2+(dy/ry)**2)
    return cx+dx*k,cy+dy*k

class Scene:
    def __init__(self,w,h,style):
        self.w,self.h=w,h;self.style=style;self.ops=[];self.boxes=[];self.counts={};self.notes=[];self.protected_segments=[];self.routes=[]
    def add(self,t,**kw):self.ops.append({'type':t,**kw})
    def rect(self,x,y,w,h,fill='white',stroke=None,sw=None,rx=0,dash=None):
        self.add('rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke or self.style['stroke'],sw=sw or self.style['line'],rx=rx,dash=dash)
    def ellipse(self,cx,cy,rx,ry,fill='white',stroke=None,sw=None,shadow=False):
        if shadow:self.add('ellipse',cx=cx+2,cy=cy+2,rx=rx,ry=ry,fill='#dddddd',stroke='none',sw=0)
        self.add('ellipse',cx=cx,cy=cy,rx=rx,ry=ry,fill=fill,stroke=stroke or self.style['stroke'],sw=sw or self.style['line'])
    def line(self,points,arrow=None,dash=False,color=None,sw=None):
        self.add('line',points=[list(p) for p in points],arrow=arrow,dash=dash,color=color or self.style['stroke'],sw=sw or self.style['line'])
    def text(self,x,y,text,size=None,anchor='middle',family=None,bold=False,color='#000000',width=None,container=None,role=None):
        size=size or self.style['size']; family=family or self.style['font']
        if width:text=wrap(text,width,size,family,bold)
        self.add('text',x=x,y=y,text=str(text),size=size,anchor=anchor,family=family,bold=bold,color=color,container=container,role=role)
    def polygon(self,points,fill='white',stroke=None,sw=None):
        self.add('polygon',points=[list(p) for p in points],fill=fill,stroke=stroke or self.style['stroke'],sw=sw or self.style['line'])
    def box(self,id,x,y,w,h,kind='node'):
        self.boxes.append({'id':id,'box':[x,y,x+w,y+h],'kind':kind})
    def frame(self,label,prefix='sd',size=None):
        self.rect(6,6,self.w-12,self.h-12)
        size=size or self.style['size'];tw=measure(prefix+' '+label,size,self.style['font'],True)[0]+25
        self.polygon([(6,6),(tw,6),(tw,22),(tw-16,36),(6,36)])
        self.text(12,10,prefix+' '+label,size=size,anchor='start',bold=True)
    def actor(self,x,y,label,scale=1,business=False,face_slash=False,color='white',name_y=None,size=None,tall=False):
        r=7*scale; self.ellipse(x,y+r,r,r,fill=color)
        knee=(5.35 if tall else 4)*r;foot=(8 if tall else 6)*r
        self.line([(x,y+2*r),(x,y+knee)]);self.line([(x-2*r,y+2.6*r),(x+2*r,y+2.6*r)])
        self.line([(x,y+knee),(x-2*r,y+foot)]); self.line([(x,y+knee),(x+2*r,y+foot)])
        if business or face_slash:
            # Course/MYY business notation: a visible diagonal across the head.
            self.line([(x-.68*r,y+1.68*r),(x+.68*r,y+.32*r)],color='#555555')
        if label:self.text(x,name_y if name_y is not None else y+foot+5,label,size=size)
    def bce(self,x,y,r,kind,label='',fill=None,size=None,shadow=None):
        fill=fill or self.style['fill'];shadow=self.style['shadow'] if shadow is None else shadow
        self.ellipse(x,y,r,r,fill=fill,shadow=shadow)
        if kind=='boundary':
            self.line([(x-r-5,y-r),(x-r-5,y+r)]);self.line([(x-r-5,y),(x-r,y)])
        elif kind=='control':self.line([(x-1,y-r-6),(x-9,y-r),(x-1,y-r+6)])
        elif kind=='entity':self.line([(x-r,y+r),(x+r,y+r)])
        elif kind in ['business-worker','business-entity']:
            self.line([(x,y+r),(x+r,y)],color='#666666')
            if kind=='business-worker':
                self.actor(x,y-r/2,'',scale=r/38)
                self.line([(x+10,y-r-9),(x,y-r),(x+10,y-r+9)],color='#666666')
        if label:self.text(x,y+r+10,label,size=size,family='Arial' if not re.search(r'[\u4e00-\u9fff]',label) else self.style['font'])
    def audit(self):
        issues=[]; textbounds=[]
        for i,o in enumerate(self.ops):
            if o['type']!='text':continue
            lines=o['text'].split('\n');width=max(measure(s,o['size'],o['family'],o['bold'])[0] for s in lines)
            height=(len(lines)-1)*o['size']*1.25+max(measure(s or ' ',o['size'],o['family'],o['bold'])[1] for s in lines)
            left=o['x']-({'middle':width/2,'end':width}.get(o['anchor'],0)); b=[left,o['y'],left+width,o['y']+height]
            textbounds.append({'op':i,'text':o['text'],'box':b})
            if b[0]<-1 or b[1]<-1 or b[2]>self.w+1 or b[3]>self.h+1:issues.append({'type':'text-outside-canvas','text':o['text'],'box':b})
            if o.get('container'):
                c=o['container']
                if b[0]<c[0]-1 or b[1]<c[1]-1 or b[2]>c[2]+1 or b[3]>c[3]+1:issues.append({'type':'text-outside-container','text':o['text'],'box':b,'container':c})
        for i,a in enumerate(self.boxes):
            x1,y1,x2,y2=a['box']
            if x1<0 or y1<0 or x2>self.w or y2>self.h:issues.append({'type':'node-outside-canvas','id':a['id']})
            for b in self.boxes[i+1:]:
                if a['kind']!=b['kind']:continue
                u1,v1,u2,v2=b['box']
                if min(x2,u2)>max(x1,u1)+1 and min(y2,v2)>max(y1,v1)+1:issues.append({'type':'node-overlap','ids':[a['id'],b['id']]})
        # Labels should never overlap one another. Nearby lines/activation bars need visual review.
        for i,a in enumerate(textbounds):
            for b in textbounds[i+1:]:
                x1,y1,x2,y2=a['box'];u1,v1,u2,v2=b['box']
                if min(x2,u2)>max(x1,u1)+2 and min(y2,v2)>max(y1,v1)+2:
                    issues.append({'type':'text-overlap','texts':[a['text'],b['text']]})
        # A fragment boundary is a structural line, not decoration: it must not
        # bisect a message label even when no two text boxes overlap.
        for a in textbounds:
            if self.ops[a['op']].get('role')!='message-label':continue
            x1,y1,x2,y2=a['box']
            for seg in self.protected_segments:
                sx1,sy1,sx2,sy2=seg['line']
                crosses=(sy1==sy2 and max(x1,sx1)+2<min(x2,sx2) and y1-2<sy1<y2+2) or (sx1==sx2 and max(y1,sy1)+2<min(y2,sy2) and x1-2<sx1<x2+2)
                if crosses:issues.append({'type':'fragment-border-crosses-label','text':a['text'],'segment':seg['name']})
        for route in self.routes:
            for node in self.boxes:
                if node['id'] in (route['from'],route['to']):continue
                bx1,by1,bx2,by2=node['box'];bx1+=2;by1+=2;bx2-=2;by2-=2
                for (x1,y1),(x2,y2) in zip(route['points'],route['points'][1:]):
                    # Liang-Barsky clipping catches diagonal as well as
                    # horizontal/vertical segments crossing a foreign class.
                    dx,dy=x2-x1,y2-y1;lo,hi=0.0,1.0;hit=True
                    for p,q in [(-dx,x1-bx1),(dx,bx2-x1),(-dy,y1-by1),(dy,by2-y1)]:
                        if p==0:
                            if q<0:hit=False;break
                        else:
                            t=q/p
                            if p<0:lo=max(lo,t)
                            else:hi=min(hi,t)
                            if lo>hi:hit=False;break
                    hit=hit and hi>max(lo,0) and lo<1
                    if hit:issues.append({'type':'class-relation-crosses-class','relation':[route['from'],route['to']],'obstacle':node['id']});break
        return {'canvas':[self.w,self.h],'counts':self.counts,'issues':issues,'notes':self.notes,'fonts':{k:font_path(k) for k in {o['family'] for o in self.ops if o['type']=='text'}},'text_bounds':textbounds,'boxes':self.boxes,'scope':'检查节点相交、文字相交、画布及指定容器溢出；不替代箭头语义、连线遮挡或字体渲染的目视校验。'}

def arrow_polygon(points,kind,sw):
    if not kind or len(points)<2:return None
    x,y=points[-1];px,py=points[-2];angle=math.atan2(y-py,x-px);L=max(8,sw*6);H=max(4,sw*3)
    bx,by=x-L*math.cos(angle),y-L*math.sin(angle)
    a=(bx+H*math.sin(angle),by-H*math.cos(angle)); b=(bx-H*math.sin(angle),by+H*math.cos(angle))
    return [a,(x,y),b] if kind=='open' else [a,(x,y),b,a]
def save_svg(s,path):
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h}" viewBox="0 0 {s.w} {s.h}">',
         '<defs><linearGradient id="peach"><stop stop-color="#fcead9"/><stop offset="1" stop-color="#fffdfb"/></linearGradient><linearGradient id="blue"><stop stop-color="#cde8fa"/><stop offset="1" stop-color="#eaf5ff"/></linearGradient></defs>',
         f'<rect width="{s.w}" height="{s.h}" fill="white"/>']
    for o in s.ops:
        t=o['type'];fill={'peach':'url(#peach)','blue':'url(#blue)'}.get(o.get('fill'),o.get('fill'))
        if t=='rect':out.append(f'<rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" rx="{o["rx"]}" fill="{fill}" stroke="{o["stroke"]}" stroke-width="{o["sw"]}"'+(' stroke-dasharray="7 5"' if o.get('dash') else '')+'/>')
        elif t=='ellipse':out.append(f'<ellipse cx="{o["cx"]}" cy="{o["cy"]}" rx="{o["rx"]}" ry="{o["ry"]}" fill="{fill}" stroke="{o["stroke"]}" stroke-width="{o["sw"]}"/>')
        elif t=='polygon':out.append(f'<polygon points="'+ ' '.join(f'{x},{y}' for x,y in o['points'])+f'" fill="{fill}" stroke="{o["stroke"]}" stroke-width="{o["sw"]}"/>')
        elif t=='line':
            out.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in o['points'])+f'" fill="none" stroke="{o["color"]}" stroke-width="{o["sw"]}"'+(' stroke-dasharray="5 4"' if o['dash'] else '')+'/>')
            a=arrow_polygon(o['points'],o['arrow'],o['sw'])
            if a:
                isopen=o['arrow']=='open';out.append(('<polyline' if isopen else '<polygon')+' points="'+' '.join(f'{x},{y}' for x,y in a)+f'" fill="'+('none' if isopen else 'white' if o['arrow']=='hollow' else o['color'])+f'" stroke="{o["color"]}" stroke-width="{o["sw"]}"/>')
        elif t=='text':
            for n,line in enumerate(o['text'].split('\n')):
                f=get_font(o['size'],o['family'],o['bold']); bb=f.getbbox(line or ' ',anchor='ls');baseline=o['y']-bb[1]+n*o['size']*1.25
                actual_family=get_font(o['size'],o['family'],o['bold']).getname()[0]
                out.append(f'<text x="{o["x"]}" y="{baseline}" text-anchor="{o["anchor"]}" font-family="{actual_family},Noto Sans CJK SC,serif" font-size="{o["size"]}" font-weight="'+('bold' if o['bold'] else 'normal')+f'" fill="{o["color"]}">{escape(line)}</text>')
    out.append('</svg>');path.write_text('\n'.join(out),encoding='utf8', newline='\n')

def save_png(s,path,scale=3):
    im=Image.new('RGB',(round(s.w*scale),round(s.h*scale)),'white');d=ImageDraw.Draw(im)
    def xy(ps):return [(round(x*scale),round(y*scale)) for x,y in ps]
    def fill_shape(box,fill,ellipse=False,rx=0):
        if fill not in ['peach','blue']:
            if fill in ['none',None]:return
            if ellipse:d.ellipse(box,fill=fill)
            elif rx:d.rounded_rectangle(box,rx*scale,fill=fill)
            else:d.rectangle(box,fill=fill)
            return
        x1,y1,x2,y2=[round(v) for v in box];w,h=max(1,x2-x1+1),max(1,y2-y1+1)
        layer=Image.new('RGB',(w,h));ld=ImageDraw.Draw(layer)
        start,end=('#fcead9','#fffdfb') if fill=='peach' else ('#cde8fa','#eaf5ff');a,b=ImageColor.getrgb(start),ImageColor.getrgb(end)
        for x in range(w):ld.line([(x,0),(x,h)],fill=tuple(round(a[i]+(b[i]-a[i])*x/max(1,w-1)) for i in range(3)))
        mask=Image.new('L',(w,h),0);md=ImageDraw.Draw(mask)
        if ellipse:md.ellipse((0,0,w-1,h-1),fill=255)
        elif rx:md.rounded_rectangle((0,0,w-1,h-1),rx*scale,fill=255)
        else:md.rectangle((0,0,w-1,h-1),fill=255)
        im.paste(layer,(x1,y1),mask)
    def line(points,color,sw,dash=False):
        ps=xy(points);width=max(1,round(sw*scale))
        if not dash:d.line(ps,fill=color,width=width,joint='curve');return
        for (x1,y1),(x2,y2) in zip(ps,ps[1:]):
            dist=math.hypot(x2-x1,y2-y1);t=0
            while t<dist:
                end=min(dist,t+5*scale)
                if dist:d.line([(x1+(x2-x1)*t/dist,y1+(y2-y1)*t/dist),(x1+(x2-x1)*end/dist,y1+(y2-y1)*end/dist)],fill=color,width=width)
                t+=9*scale
    for o in s.ops:
        t=o['type']
        if t in ['rect','ellipse']:
            if t=='rect':box=[o['x']*scale,o['y']*scale,(o['x']+o['w'])*scale,(o['y']+o['h'])*scale]
            else:box=[(o['cx']-o['rx'])*scale,(o['cy']-o['ry'])*scale,(o['cx']+o['rx'])*scale,(o['cy']+o['ry'])*scale]
            fill_shape(box,o['fill'],t=='ellipse',o.get('rx',0))
            if o['stroke']!='none':
                width=max(1,round(o['sw']*scale))
                if t=='ellipse':d.ellipse(box,outline=o['stroke'],width=width)
                elif o.get('dash'):
                    x,y,w,h=o['x'],o['y'],o['w'],o['h'];line([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)],o['stroke'],o['sw'],True)
                elif o.get('rx'):d.rounded_rectangle(box,o['rx']*scale,outline=o['stroke'],width=width)
                else:d.rectangle(box,outline=o['stroke'],width=width)
        elif t=='polygon':d.polygon(xy(o['points']),fill=o['fill'] if o['fill']!='none' else None);line(o['points']+[o['points'][0]],o['stroke'],o['sw'])
        elif t=='line':
            line(o['points'],o['color'],o['sw'],o['dash']);a=arrow_polygon(o['points'],o['arrow'],o['sw'])
            if a:
                if o['arrow']=='open':line(a,o['color'],o['sw'])
                else:d.polygon(xy(a),fill='white' if o['arrow']=='hollow' else o['color']);line(a,o['color'],o['sw'])
        elif t=='text':
            f=get_font(o['size'],o['family'],o['bold'],scale)
            for n,l in enumerate(o['text'].split('\n')):
                bb=f.getbbox(l or ' ',anchor='ls');w=f.getlength(l);x=o['x']*scale-({'middle':w/2,'end':w}.get(o['anchor'],0));y=o['y']*scale-bb[1]+n*o['size']*1.25*scale
                d.text((x,y),l,font=f,fill=o['color'],anchor='ls',stroke_width=max(1,round(.3*scale)) if o['bold'] and o['family']!='Arial' else 0)
    im.save(path,dpi=(300,300))

def save_drawio(s,path):
    """Editable vector primitives, never a raster picture disguised as a diagram."""
    mx=ET.Element('mxfile',host='app.diagrams.net');dg=ET.SubElement(mx,'diagram',id='report',name='报告图片')
    model=ET.SubElement(dg,'mxGraphModel',dx=str(s.w),dy=str(s.h),grid='0',page='1',pageWidth=str(s.w),pageHeight=str(s.h));root=ET.SubElement(model,'root')
    ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    for i,o in enumerate(s.ops,2):
        typ=o['type'];attrs={'id':str(i),'parent':'1','value':''};style='html=0;'
        if typ=='line':
            attrs['edge']='1';style+='endArrow='+({'filled':'block','hollow':'block','open':'open'}.get(o['arrow'],'none'))+';endFill='+('0' if o['arrow'] in ['hollow','open'] else '1')+f';strokeColor={o["color"]};strokeWidth={o["sw"]};'
            if o['dash']:style+='dashed=1;'
            attrs['style']=style;cell=ET.SubElement(root,'mxCell',**attrs);g=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
            ET.SubElement(g,'mxPoint',x=str(o['points'][0][0]),y=str(o['points'][0][1]),**{'as':'sourcePoint'})
            ET.SubElement(g,'mxPoint',x=str(o['points'][-1][0]),y=str(o['points'][-1][1]),**{'as':'targetPoint'})
            if len(o['points'])>2:
                a=ET.SubElement(g,'Array',**{'as':'points'})
                for x,y in o['points'][1:-1]:ET.SubElement(a,'mxPoint',x=str(x),y=str(y))
            continue
        attrs['vertex']='1'
        if typ=='text':
            lines=o['text'].split('\n');w=max(measure(l,o['size'],o['family'],o['bold'])[0] for l in lines)+4;h=len(lines)*o['size']*1.25+3
            x=o['x']-({'middle':w/2,'end':w}.get(o['anchor'],0));y=o['y']-2
            attrs['value']=o['text'];style+=f'text;strokeColor=none;fillColor=none;align='+({'middle':'center','end':'right'}.get(o['anchor'],'left'))+f';verticalAlign=top;spacing=0;fontFamily={o["family"]};fontSize={o["size"]};fontColor={o["color"]};fontStyle='+('1' if o['bold'] else '0')+';whiteSpace=wrap;'
        elif typ=='rect':
            x,y,w,h=o['x'],o['y'],o['w'],o['h'];style+='rounded='+('1' if o.get('rx') else '0')+';'
        elif typ=='ellipse':x,y,w,h=o['cx']-o['rx'],o['cy']-o['ry'],o['rx']*2,o['ry']*2;style+='ellipse;'
        elif typ=='polygon':
            # Frame tabs can be approximated by draw.io's native note shape; SVG is the precise master.
            xs,ys=zip(*o['points']);x,y=min(xs),min(ys);w,h=max(xs)-x,max(ys)-y;style+=('rhombus;' if len(o['points'])==4 else 'shape=note;size=16;')
        else:continue
        if typ!='text':
            fill={'peach':'#fcead9','blue':'#cde8fa'}.get(o['fill'],o['fill']);style+=f'fillColor={fill};strokeColor={o["stroke"]};strokeWidth={o["sw"]};'
            if o['fill'] in ['peach','blue']:style+='gradientColor=#ffffff;gradientDirection=east;'
            if o.get('dash'):style+='dashed=1;'
        attrs['style']=style;cell=ET.SubElement(root,'mxCell',**attrs);ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    ET.indent(mx);ET.ElementTree(mx).write(path,encoding='utf-8',xml_declaration=True)

def save_plantuml(m,path):
    """Emit a separate semantic cross-check, not a pixel-equivalent reconstruction."""
    typ=m['type']
    if typ not in ('usecase','sequence','class'):return
    q=lambda value: str(value).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
    out=['@startuml','skinparam backgroundColor white','skinparam shadowing false']
    if typ=='usecase':
        actors={a['id']:f'A{i}' for i,a in enumerate(m['actors'])}
        usecases={u['id']:f'U{i}' for i,u in enumerate(m['usecases'])}
        for a in m['actors']:
            if a.get('kind')=='external-system':
                out.append(f'rectangle "«actor»\\n{q(a["label"])}" as {actors[a["id"]]}')
            else:
                out.append(f'actor "{q(a["label"])}" as {actors[a["id"]]}')
        out.append(f'rectangle "{q(m.get("system","系统"))}" {{')
        for u in m['usecases']:out.append(f'  usecase "{q(u["label"])}" as {usecases[u["id"]]}')
        out.append('}')
        for u in m['usecases']:
            for a in u.get('actors',[]):
                edge='-->' if m.get('directed_associations',False) else '--'
                out.append(f'{actors[a]} {edge} {usecases[u["id"]]}')
        for r in m.get('relations',[]):
            kind=r['kind'];edge='..>' if kind in ('include','extend') else '--|>' if kind=='generalization' else '--'
            suffix=f' : <<{kind}>>' if kind in ('include','extend') else ''
            out.append(f'{usecases[r["from"]]} {edge} {usecases[r["to"]]}{suffix}')
    elif typ=='sequence':
        if m.get('title'):out.append(f'title {q(m["title"])}')
        for p in m['participants']:
            kind=p.get('kind','participant');keyword=kind if kind in ('actor','boundary','control','entity') else 'participant'
            stereotype=''
            if kind=='business-worker':keyword='actor';stereotype=' <<业务工人>>'
            elif kind=='business-entity':stereotype=' <<业务实体>>'
            out.append(f'{keyword} "{q(p["label"])}" as {p["id"]}{stereotype}')
        starts={};ends={};branches={}
        for f in m.get('fragments',[]):
            starts.setdefault(f['start'],[]).append(f);ends.setdefault(f['end'],[]).append(f)
            for op in f.get('operands',[])[1:]:branches.setdefault(op['start'],[]).append(op)
        for i,e in enumerate(m['messages']):
            for f in starts.get(i,[]):
                ops=f.get('operands',[]);guard='['+q(ops[0]['guard'])+']' if ops else q(f.get('label',''))
                out.append(f'{f.get("operator","alt")} {guard}')
            for op in branches.get(i,[]):out.append(f'else [{q(op["guard"])}]')
            edge='-->' if e.get('kind')=='return' else '->>' if e.get('kind')=='async' else '->'
            out.append(f'{e["from"]} {edge} {e["to"]}: {q(e["label"])}')
            for f in reversed(ends.get(i,[])):out.append('end')
    else:
        for c in m['classes']:
            out.append(f'class "{q(c["name"])}" as {c["id"]} {{')
            for a in c.get('attributes',[]):
                visibility=a.get('visibility','')
                out.append('  '+visibility+a['name']+(': '+a['type'] if a.get('type') else ''))
            if c.get('methods'):out.append('  --')
            for method in c.get('methods',[]):out.append('  '+(method if isinstance(method,str) else method.get('signature','')))
            out.append('}')
        for c in m['classes']:
            if c.get('parent'):out.append(f'{c["parent"]} <|-- {c["id"]}')
        relation_edge={'association':'--','aggregation':'o--','composition':'*--','dependency':'..>','realization':'..|>','generalization':'--|>'}
        for r in m.get('relations',[]):
            edge=relation_edge[r.get('kind','association')]
            fm=' "'+q(r['from_multiplicity'])+'"' if r.get('from_multiplicity') else ''
            tm='"'+q(r['to_multiplicity'])+'" ' if r.get('to_multiplicity') else ''
            label=' : '+q(r['label']) if r.get('label') else ''
            out.append(f'{r["from"]}{fm} {edge} {tm}{r["to"]}{label}')
    out.append('@enduml')
    path.write_text('\n'.join(out)+'\n',encoding='utf8', newline='\n')

def render_usecase(m,st):
    b=st is not None and m.get('profile')=='b-enterprise';size=m.get('font_size',st['size']);actors=m['actors'];ucs=m['usecases']
    ew=m.get('ellipse_width',max(140 if not b else 106,max(measure(u['label'],size,st['font'],b)[0] for u in ucs)+32));eh=m.get('ellipse_height',50 if not b else 70)
    gap=m.get('row_gap',70 if not b else 94);margin=80 if not b else 95
    # Rows/columns are logical ranks. Column 0 is the main fan; related use cases occupy column 1+.
    maxrow=max(u.get('row',i) for i,u in enumerate(ucs));maxcol=max(u.get('column',0) for u in ucs)
    w=m.get('width',max(580,margin+160+(maxcol+1)*(ew+100)) if not b else max(810,250+(maxcol+1)*(ew+115)+130));h=m.get('height',max(300,(153 if b else 110)+maxrow*gap+eh))
    s=Scene(w,h,st)
    if b:s.frame(m.get('title','系统用例图'),'uc')
    bx,by,bw,bh=m.get('boundary',[93 if not b else 225,0 if not b else 43,w-(173 if not b else 260),h-(0 if not b else 74)])
    s.rect(bx,by,bw,bh,rx=2 if b else 0);sx,sy=m.get('system_position',[bx+bw/2,by+(30 if not b else 6)]);s.text(sx,sy,m.get('system','系统名称'),size=m.get('system_font_size',size),bold=m.get('system_bold',False))
    centers={}
    for i,u in enumerate(ucs):
        x,y=u.get('center',[bx+bw/(maxcol+2)+u.get('column',0)*bw/(maxcol+2),by+85+u.get('row',i)*gap]);rw=u.get('width',ew);rh=u.get('height',eh)
        centers[u['id']]=(x,y,rw/2,rh/2)
        if x-rw/2<bx or x+rw/2>bx+bw or y-rh/2<by or y+rh/2>by+bh:
            raise ValueError('用例 '+u['id']+' 超出系统边界；增大画布/边界或重新安排行列。')
    ac={}
    for i,a in enumerate(actors):
        targets=[centers[u['id']] for u in ucs if a['id'] in u.get('actors',[])]
        ay=(min(p[1] for p in targets)+max(p[1] for p in targets))/2 if targets else h/2
        ax,ay=a.get('center',[bx-65,ay]);ac[a['id']]=(ax,ay)
        if a.get('kind')=='external-system':
            # The course's non-human business-entity glyph is a circle with a slash.
            # Its Chinese role label distinguishes it from a human actor.
            radius=a.get('radius',27);cy=ay-13
            s.ellipse(ax,cy,radius,radius,fill='white',sw=1.4)
            s.line([(ax,cy+radius),(ax+radius,cy)],color='#444444',sw=1.4)
            s.line([(ax-radius-2,cy+radius+1),(ax+radius+2,cy+radius+1)],sw=1.2)
            s.text(ax,ay+22,a['label'],size=a.get('font_size',size)*.77,bold=True)
            s.box(a['id'],ax-radius,cy-radius,radius*2,radius*2,kind='external-actor')
        else:
            s.actor(ax,a.get('top',ay-32 if b else ay-29),a['label'],scale=a.get('scale',.9 if b else 1.1),business=a.get('business',False),face_slash=a.get('face_slash',False),color='#f7dbaa' if b else 'white',size=a.get('font_size',size),name_y=a.get('name_y'),tall=not b)
    association_count=0
    fan_indexes={a['id']:0 for a in actors};actor_items={a['id']:a for a in actors}
    for u in ucs:
        x,y,rx,ry=centers[u['id']]
        for aid in u.get('actors',[]):
            ax,ay=ac[aid]
            actor=actor_items[aid]
            n=sum(aid in item.get('actors',[]) for item in ucs)
            if actor.get('kind')=='external-system':
                radius=actor.get('radius',27);cy=ay-13
                fanstep=min(actor.get('fan_step',8),radius/max(n,1))
                fan_y=cy+(fan_indexes[aid]-(n-1)/2)*fanstep
                start=(ax-radius if ax>x else ax+radius,fan_y)
            else:
                radius=7*actor.get('scale',.9 if b else 1.1)
                top=actor.get('top',ay-32 if b else ay-29)
                # Associations touch the actor body, not a disconnected point.
                spine_mid=top+3.7*radius
                available=3.1*radius
                requested=actor.get('fan_step',5 if n>1 else 0)
                fanstep=min(requested,available/max(n-1,1))
                fan_y=spine_mid+(fan_indexes[aid]-(n-1)/2)*fanstep
                start=(ax,fan_y)
            fan_indexes[aid]+=1
            bends=m.get('association_routes',{}).get(aid+':'+u['id'],[])
            end=port(x,y,rx,ry,*(bends[-1] if bends else start))
            directed=not b and m.get('directed_associations',bool(m.get('source_trace')))
            s.line([start,*bends,end],arrow=m.get('association_arrow','open') if directed else None);association_count+=1
    for r in m.get('relations',[]):
        a=centers[r['from']];v=centers[r['to']];start=port(*a,v[0],v[1]);end=port(*v,a[0],a[1]);kind=r['kind']
        s.line([start,end],arrow='hollow' if kind=='generalization' else 'open' if kind in ['include','extend'] else None,dash=kind in ['include','extend'])
        if kind in ['include','extend']:
            px,py=r.get('label_position',[(start[0]+end[0])/2,(start[1]+end[1])/2+7]);s.text(px,py,'«'+kind+'»',size=size*.72,family='Arial')
    for u in ucs:
        x,y,rx,ry=centers[u['id']];s.ellipse(x,y,rx,ry,fill='blue' if b else 'white',shadow=b)
        if u.get('business',False) or m.get('ellipse_slash',False):
            # A short lower-right chord: both ends lie on the ellipse.
            # Floating strokes inside an oval are visually ambiguous.
            lower_angle,upper_angle=map(math.radians,m.get('ellipse_slash_angles',[35,0]))
            s.line([(x+rx*math.cos(lower_angle),y+ry*math.sin(lower_angle)),
                    (x+rx*math.cos(upper_angle),y+ry*math.sin(upper_angle))],color='#555555',sw=1.3)
        label=wrap(u['label'],rx*2-20,size,st['font'],b);lh=len(label.split('\n'))*size*1.25;s.text(x,y-lh/2+2,label,size=size,bold=b,container=[x-rx+7,y-ry+5,x+rx-7,y+ry-5]);s.box(u['id'],x-rx,y-ry,rx*2,ry*2)
    s.counts={'actors':len(actors),'usecases':len(ucs),'associations':association_count,'relations':len(m.get('relations',[]))};return s

def render_sequence(m,st):
    b=m.get('profile')=='b-enterprise';ps=m['participants'];events=m['messages'];size=m.get('font_size',st['size']);top=m.get('message_top',150 if b else 180);step=m.get('message_gap',44 if b else 40)
    # Adjacent gap is driven by the widest message/header needing that span, with room for self calls.
    gaps=[]
    for i in range(len(ps)-1):
        labels=[e['label'] for e in events if {e['from'],e['to']}=={ps[i]['id'],ps[i+1]['id']}]
        selflabels=[e['label'] for e in events if e['from']==e['to']==ps[i]['id']]
        gap=max(m.get('lane_gap',175 if b else 180),max([measure(l.split('\n')[0],size,st['font'])[0]+36 for l in labels]+[0]),max([max(measure(t,size,st['font'])[0] for t in l.split('\n'))+75 for l in selflabels]+[0]))
        gaps.append(gap)
    xs=[m.get('first_lane',80 if b else 50)]
    for gap in gaps:xs.append(xs[-1]+gap)
    for i,p in enumerate(ps):
        if 'x' in p:xs[i]=p['x']
    ys=[];current=top
    fragment_starts={f['start'] for f in m.get('fragments',[]) if 'y' not in f}
    operand_starts={op['start'] for f in m.get('fragments',[]) for op in f.get('operands',[])[1:] if 'y' not in op}
    for ei,e in enumerate(events):
        if 'y' not in e:
            if ei in fragment_starts:current+=70
            elif ei in operand_starts:current+=40
        y=e.get('y',current);ys.append(y)
        lines=e['label'].count('\n')+1
        # Self-call labels are placed beside a return loop, below the message.
        # Reserve an extra baseline before the next inter-lifeline message.
        current=y+max(step,lines*size*1.25+50 if e['from']==e['to'] else lines*size*1.25+18)
    h=m.get('height',max(ys+[top])+max(85,step*1.5))
    extra=max([xs[ps.index(next(p for p in ps if p['id']==e['from']))]+e.get('loop_width',40)+25+max(measure(line,size,st['font'])[0] for line in e['label'].split('\n')) for e in events if e['from']==e['to']]+[xs[-1]+80])
    w=m.get('width',max(xs[-1]+100,extra+20))
    s=Scene(w,h,st)
    if b and m.get('frame',True):s.frame(m.get('title','交互序列图'),'sd',size=m.get('frame_font_size'))
    pid={p['id']:i for i,p in enumerate(ps)};last=m.get('lifeline_end',h-45 if b else h-4);headbottom=m.get('lifeline_start',130 if b else 141)
    for i,p in enumerate(ps):
        x=xs[i];kind=p.get('kind','entity')
        if not b:
            if kind=='actor':s.actor(x,30,'',scale=1.05,tall=True)
            else:s.bce(x,50,40,kind,fill='white',shadow=False)
            head_width=max(100,measure(p['label'],size,st['font'])[0]+20)
            s.rect(x-head_width/2,100,head_width,40)
            s.text(x,114,p['label'],size=size,container=[x-head_width/2+2,101,x+head_width/2-2,139])
        else:
            r=p.get('radius',22)
            if kind=='actor':
                business=p.get('business',False) or 'business actor' in p['label']
                s.actor(x,p.get('actor_top',55 if business else 43),'',scale=p.get('actor_scale',.9 if business else .67),business=business,color='#fce5c4')
                s.text(x,p.get('name_y',108 if business else 83),p['label'],size=p.get('label_size',size if business else size*.82),family='Arial' if not re.search(r'[\u4e00-\u9fff]',p['label']) else st['font'])
            elif kind in ['department','system']:
                s.bce(x,85,r, 'entity',fill='#b9e6e8');s.text(x,119,p['label'],size=size)
            elif kind=='entity':
                label_size=p.get('label_size',size*.8)
                label_family='Arial' if not re.search(r'[\u4e00-\u9fff]',p['label']) else st['font']
                ew=p.get('width',50 if m.get('source_trace') else max(50,measure(p['label'],label_size,label_family)[0]+16))
                s.rect(x-ew/2,43,ew,50,fill='peach',rx=2);s.text(x,49,p['label'],size=label_size,family=label_family,width=ew-8,container=[x-ew/2+3,45,x+ew/2-3,91])
            else:
                label_family='Arial' if not re.search(r'[\u4e00-\u9fff]',p['label']) else st['font']
                s.bce(x,64,r,kind,fill='peach');s.text(x,94,p['label'],size=p.get('label_size',size*.75),family=label_family)
            if p.get('origin'):
                s.text(x,p.get('origin_y',104),'(from '+p['origin']+')',size=p.get('origin_size',size*.75),width=p.get('origin_width',100))
        s.line([(x,headbottom),(x,last)],dash=True)
    # Fragment backgrounds/guards before messages; border overlaid after activations.
    fragments=[]
    for f in m.get('fragments',[]):
        ia,ib=pid[f['from']],pid[f['to']];guardwidth=max([measure('['+o['guard']+']',size,st['font'])[0] for o in f.get('operands',[])]+[0])
        # A combined fragment must cover every lifeline involved in its operands,
        # not merely the two lanes named in a convenient JSON bounding hint.
        involved={ia,ib}
        for event in events[f['start']:f['end']+1]:
            involved.add(pid[event['from']]);involved.add(pid[event['to']])
        x1=f.get('x',max(12,min(xs[i] for i in involved)-max(55,guardwidth+22)))
        x2=f.get('right',max(xs[i] for i in involved)+45)
        y1=f.get('y',ys[f['start']]-65);y2=f.get('bottom',ys[f['end']]+32)
        # The original screenshots sometimes let an alt frame cut through a
        # boundary-to-control message.  Keep their JSON coordinates as evidence,
        # but widen the rendered frame to cover every participating lifeline.
        tabwidth=measure(f.get('operator','alt')+' '+f.get('label',''),size,st['font'],True)[0]+20
        required_left=max(12,min(xs[i] for i in involved)-max(45,guardwidth+18,tabwidth+18))
        required_right=max(xs[i] for i in involved)+45
        if x1>required_left or x2<required_right:
            s.notes.append(f"片段 {f.get('label','')} 外框扩至全部交互生命线；原图坐标仅作风格参考。")
            x1=min(x1,required_left);x2=max(x2,required_right)
        if f['start']:
            prev=events[f['start']-1];py=ys[f['start']-1]
            if prev['from']==prev['to']:
                label_y=prev.get('label_position',[0,py+7])[1]
                label_bottom=label_y+(prev['label'].count('\n')+1)*size*1.25
                safe_top=max(py+prev.get('loop_height',22 if b else 26)+10,label_bottom+9)
                if y1<safe_top:
                    y1=safe_top;s.notes.append(f"片段 {f.get('label','')} 下移，避开前一条自调用和文字。")
        fragments.append((f,x1,x2,y1,y2));
    # Explicit activation intervals are part of trace examples. New models can infer intervals from events.
    acts=m.get('activations')
    if acts is not None:
        resolved=[]
        for interval in acts:
            a=dict(interval)
            if 'start_message' in a:
                first,last_index=a['start_message'],a.get('end_message',a['start_message'])
                if not (0<=first<=last_index<len(events)):
                    raise ValueError('激活区间的消息索引超出范围或次序错误。')
                a['y']=ys[first]+a.get('start_offset',0)
                a['end']=ys[last_index]+a.get('end_offset',12)
            if 'y' not in a or 'end' not in a or a['end']<=a['y']:
                raise ValueError('激活区间必须具有正的执行长度。')
            resolved.append(a)
        acts=resolved
    if acts is None:
        intervals={p['id']:[] for p in ps};split=m.get('activation_split_gap',step*2.5)
        for p in ps:
            inds=[i for i,e in enumerate(events) if p['id'] in [e['from'],e['to']]]
            if not inds:continue
            if p.get('kind')=='actor':continue
            groups=[]
            for ix in inds:
                if groups and ys[ix]-groups[-1][-1]<split:groups[-1].append(ys[ix])
                else:groups.append([ys[ix]])
            intervals[p['id']]=[(g[0],g[-1]+18) for g in groups]
        acts=[{'participant':k,'y':a,'end':v} for k,it in intervals.items() for a,v in it]
        s.notes.append('激活条为事件接触区间的布局推断。需核对实际调用栈，可用 activations 显式覆盖。')
    aw=m.get('activation_width',9 if b else 10)
    for a in acts:
        x=xs[pid[a['participant']]]+a.get('offset',0);p=ps[pid[a['participant']]];fill=a.get('fill','#fce5b7' if b and p.get('kind')=='actor' else '#b9e6e8' if p.get('kind') in ['department','system'] else 'white')
        s.rect(x-aw/2,a['y'],aw,a['end']-a['y'],fill=fill,rx=2 if b else 0)
    def active_at(id,y):return any(a['participant']==id and a['y']-1<=y<=a['end']+1 for a in acts)
    for i,e in enumerate(events):
        y=ys[i];fi,ti=pid[e['from']],pid[e['to']];x1,x2=xs[fi],xs[ti];selfcall=fi==ti;kind=e.get('kind','call');arrow='open' if kind in ['return','async'] else 'filled';dash=kind=='return'
        if selfcall:
            loop=e.get('loop_width',40 if b else 35);start=x1+aw/2 if active_at(e['from'],y) else x1;ret=y+e.get('loop_height',22 if b else 26)
            # Draw the nested activation before the self-message path.  The
            # former order placed a small rectangle on top of the arrowhead,
            # which looked like an unexplained square in the final diagram.
            # A narrow vertical bar is the UML execution occurrence; the
            # message arrow remains fully visible above it.
            if m.get('nested_self_activation',True):
                nested_fill='#fce5b7' if b and ps[fi].get('kind')=='actor' else '#b9e6e8' if ps[fi].get('kind') in ['department','system'] else 'white'
                nested_h=max(20,ret-y+8)
                s.rect(start-2,y+1,aw,nested_h,fill=nested_fill,rx=1 if b else 0)
            s.line([(start,y),(start+loop,y),(start+loop,ret),(start,ret)],arrow=arrow,dash=dash)
            labelx,labely=e.get('label_position',[start+loop+8,y+7]);s.text(labelx,labely,e['label'],size=size,anchor=e.get('label_anchor','start'),role='message-label')
        else:
            direction=1 if x2>x1 else -1;start=x1+direction*aw/2 if active_at(e['from'],y) else x1;end=x2-direction*aw/2 if active_at(e['to'],y) else x2
            s.line([(start,y),(end,y)],arrow=arrow,dash=dash)
            label=e['label'];lh=(label.count('\n')+1)*size*1.25;labelx,labely=e.get('label_position',[(start+end)/2,y-lh-3]);s.text(labelx,labely,label,size=size,anchor=e.get('label_anchor','middle'),role='message-label')
            if b and not active_at(e['to'],y):s.rect(end-4,y-4,8,10,rx=2,fill='#fce5b7' if ps[ti].get('kind')=='actor' else 'white')
    for f,x1,x2,y1,y2 in fragments:
        s.rect(x1,y1,x2-x1,y2-y1,fill='none');label=f.get('operator','alt')+' '+f.get('label','');tw=measure(label,size,st['font'],True)[0]+20
        for name,line in [('top',(x1,y1,x2,y1)),('bottom',(x1,y2,x2,y2)),('left',(x1,y1,x1,y2)),('right',(x2,y1,x2,y2))]:
            s.protected_segments.append({'name':f"{f.get('label','')}:{name}",'line':line})
        s.polygon([(x1,y1),(x1+tw,y1),(x1+tw,y1+10),(x1+tw-14,y1+21),(x1,y1+21)],fill='#f7dca2');s.text(x1+4,y1+3,label,size=size,bold=True,anchor='start')
        for n,op in enumerate(f.get('operands',[])):
            yy=op.get('y',ys[op['start']]-40)
            if n==0 and yy<y1+26:
                yy=y1+26
                s.notes.append(f"片段 {f.get('label','')} 首个分支条件下移，避开折角标题。")
            if n:
                s.line([(x1,yy-8),(x2,yy-8)],dash=True)
                s.protected_segments.append({'name':f"{f.get('label','')}:operand-{n}",'line':(x1,yy-8,x2,yy-8)})
            if m.get('source_trace'):
                guard_x=x1+5
            else:
                covered=[pid[event[k]] for event in events[f['start']:f['end']+1] for k in ('from','to')]
                guard_x=max(x1+5,min(xs[i] for i in covered)+18)
            s.text(guard_x,yy,'['+op['guard']+']',size=size,anchor='start')
    s.counts={'participants':len(ps),'messages':len(events),'self_calls':sum(e['from']==e['to'] for e in events),'returns':sum(e.get('kind')=='return' for e in events),'fragments':len(fragments),'activations':len(acts)}
    return s

def render_bce(m,st):
    labels=m['items'];kind=m['kind'];cols=m.get('columns',5);r=m.get('radius',54);size=m.get('font_size',14)
    widest=max(measure(it if isinstance(it,str) else it['label'],size,'Arial' if not re.search(r'[\u4e00-\u9fff]',it if isinstance(it,str) else it['label']) else st['font'])[0] for it in labels)
    gapx=m.get('column_gap',max(210,widest+30));gapy=m.get('row_gap',180);x0=m.get('first_x',max(105,widest/2+25));y0=m.get('first_y',112)
    rows=math.ceil(len(labels)/cols);w=m.get('width',x0+(cols-1)*gapx+max(r+55,widest/2+25));h=m.get('height',y0+(rows-1)*gapy+r+70);s=Scene(w,h,st);s.frame(m.get('title','边界类图' if kind=='boundary' else '控制类图'),'class')
    for i,item in enumerate(labels):
        if isinstance(item,str):item={'label':item}
        x,y=item.get('center',[x0+i%cols*gapx,y0+i//cols*gapy]);rr=item.get('radius',r)
        s.bce(x,y,rr,kind,fill='peach',label=item['label'],size=size);s.box(item.get('id',str(i)),x-rr-6,y-rr,rr*2+6,rr*2+size+15)
    s.counts={kind:len(labels)};return s

def class_metrics(c,size,source_trace=False):
    # Deliberately maintain two aligned columns, not arbitrary padding with spaces.
    attrs=c.get('attributes',[]);methods=c.get('methods',[]);row=c.get('row_height',size*1.5);head=c.get('header_height',size*1.9)
    names=[a['name'] for a in attrs];types=[a.get('type','') for a in attrs]
    if source_trace:
        nw=max([measure(t,size,'Arial')[0] for t in names]+[60]);tw=max([measure(t,size,'Arial')[0] for t in types]+[40]);width=max(c.get('min_width',210),nw+tw+65,measure(c['name'],size*1.2,'Arial')[0]+80, max([measure(t,size,'Arial')[0]+65 for t in methods]+[0]))
    else:
        entries=[(a.get('visibility','')+' ' if a.get('visibility') else '')+a['name']+(': '+a['type'] if a.get('type') else '') for a in attrs]
        entries += [t if isinstance(t,str) else t.get('signature','') for t in methods]
        width=max(c.get('min_width',210),measure(c['name'],size*1.2,label_family(c['name']))[0]+30,max([measure(t,size,label_family(t))[0]+28 for t in entries]+[0]))
    height=head+(len(attrs)+len(methods))*row
    return c.get('width',width),c.get('height',height),row,head
def render_classes(m,st):
    cs=m['classes'];size=m.get('font_size',16);trace=bool(m.get('source_trace'));clean=bool(m.get('clean_association_view'));semantic=bool(m.get('semantic_relationship_view'));metrics={c['id']:class_metrics(c,size,trace) for c in cs};gap=m.get('gap',55 if trace else 95);cols=m.get('columns',4)
    # Rank/shelf layout. Explicit positions preserve the source's nonuniform packing.
    ranks={}
    cmap={c['id']:c for c in cs};parentids={c['parent'] for c in cs if c.get('parent')}
    def rankof(c):
        if 'rank' in c:return c['rank']
        if c.get('parent'):return rankof(cmap[c['parent']])+1
        return 0 if c['id'] in parentids else 1
    for c in cs:ranks.setdefault(rankof(c),[]).append(c)
    pos={};cury=25;maxright=0
    for rank,items in sorted(ranks.items()):
        for start in range(0,len(items),cols):
            rowitems=items[start:start+cols];x=25;mh=max(metrics[c['id']][1] for c in rowitems)
            for c in rowitems:
                w,h,*_=metrics[c['id']];cx,cy=c.get('position',[x,cury]);pos[c['id']]=(cx,cy);x+=w+gap;maxright=max(maxright,cx+w)
            cury+=mh+gap
    # A parent on its own rank is placed over its children, keeping the inheritance fork compact.
    for c in cs:
        if c.get('center_over') and 'position' not in c:
            children=[x for x in cs if x.get('parent')==c['id']]
            if children:
                centers=[pos[x['id']][0]+metrics[x['id']][0]/2 for x in children];pos[c['id']]=((min(centers)+max(centers))/2-metrics[c['id']][0]/2,pos[c['id']][1])
    w=m.get('width',maxright+25);h=m.get('height',max(pos[c['id']][1]+metrics[c['id']][1] for c in cs)+25);s=Scene(w,h,st)
    inherit={}
    for c in cs:
        if c.get('parent'):inherit.setdefault(c['parent'],[]).append(c['id'])
    for parent,kids in inherit.items():
        px,py=pos[parent];pw,ph,*_=metrics[parent];target=(px+pw/2,py+ph);cy=min(pos[k][1] for k in kids);bus=m.get('inheritance_bus_y',(target[1]+cy)/2);color=m.get('inheritance_color','#31258b')
        xx=[pos[k][0]+metrics[k][0]/2 for k in kids];s.line([(min(xx+[target[0]]),bus),(max(xx+[target[0]]),bus)],color=color)
        s.line([(target[0],bus),target],arrow='filled' if m.get('source_trace') else 'hollow',color=color)
        for k,x in zip(kids,xx):s.line([(x,bus),(x,pos[k][1])],color=color)
    for c in cs:
        x,y=pos[c['id']];cw,ch,row,head=metrics[c['id']];presentation=clean or semantic;border='#5d6a70' if presentation else '#d0d0d0';line_width=1.35 if presentation else None;s.rect(x,y,cw,ch,stroke=border,sw=line_width);s.rect(x,y,cw,head,fill=c.get('fill','#e9f0f4') if presentation else '#e0e0e0',stroke=border,sw=line_width)
        # Trace mode reproduces the IDE screenshot. A new report uses UML compartments.
        cx=x+cw/2
        if trace:
            titlewidth=measure(c['name'],size*1.2,'Arial')[0];badge=cx-titlewidth/2-26
            s.ellipse(badge,y+head/2,8,8,fill='#8bd4e4',stroke='none');s.text(badge,y+head/2-5,'C',size=11,family='Arial',color='#47849b',bold=True);s.text(cx+10,y+head/2-size*.6,c['name'],size=size*1.2,family='Arial',color=c.get('title_color','#242424'),container=[x+35,y+2,x+cw-4,y+head-2])
        else:
            s.text(cx,y+head/2-size*.6,c['name'],size=size*1.2,family=label_family(c['name']),bold=True,container=[x+8,y+2,x+cw-8,y+head-2])
        yy=y+head
        if trace:
            entries=[]
            # Source IDE output puts serialVersionUID before the constructor, then properties.
            special=[a for a in c.get('attributes',[]) if a.get('kind')=='field'];attrs=[a for a in c.get('attributes',[]) if a.get('kind')!='field']
            entries += [('f',a['name'],a.get('type','')) for a in special]
            entries += [('m',method,'') for method in c.get('methods',[])]
            entries += [('p',a['name'],a.get('type','')) for a in attrs]
            for j,(badge,name,typ) in enumerate(entries):
                if badge in ['f','m'] or (j and entries[j-1][0] in ['f','m']):s.line([(x,yy),(x+cw,yy)],color=border)
                cc={'p':'#d6b4eb','m':'#f5bccb','f':'#f0cc89'}[badge];s.ellipse(x+16,yy+row/2,7,7,fill=cc,stroke='none');s.text(x+16,yy+row/2-5,badge,size=11,family='Arial',color='#777777')
                s.rect(x+29,yy+row/2-3,5,6,fill='#8bc87c',stroke='none');s.text(x+42,yy+row/2-size/2,name,size=size,family='Arial',anchor='start',container=[x+38,yy,x+cw-8,yy+row]);s.text(x+cw-8,yy+row/2-size/2,typ,size=size,family='Arial',anchor='end',container=[x+38,yy,x+cw-4,yy+row]);yy+=row
        else:
            for a in c.get('attributes',[]):
                label=(a.get('visibility','')+' ' if a.get('visibility') else '')+a['name']+(': '+a['type'] if a.get('type') else '')
                s.text(x+12,yy+row/2-size/2,label,size=size,family=label_family(label),anchor='start',container=[x+8,yy,x+cw-8,yy+row]);yy+=row
            if c.get('methods'):
                s.line([(x,yy),(x+cw,yy)],color=border)
                for method in c['methods']:
                    label=method if isinstance(method,str) else method.get('signature','')
                    s.text(x+12,yy+row/2-size/2,label,size=size,family=label_family(label),anchor='start',container=[x+8,yy,x+cw-8,yy+row]);yy+=row
        if c.get('selected') and m.get('source_trace'):
            s.rect(x,y,cw,ch,fill='none',stroke='#e7cb54')
            for px in [x,x+cw/2,x+cw]:
                for py in [y,y+ch]:s.rect(px-3,py-3,6,6,fill='#bcbcbc',stroke='none')
        s.box(c['id'],x,y,cw,ch)
    if clean:
        # A deliberately simplified relationship overview. The model retains
        # exact relation kinds and cardinalities; the accompanying table states
        # them, while this view uses one plain navigability arrow per relation.
        relations=m.get('relations',[])
        side_links={}
        def side_for(a,b):
            ax,ay=pos[a];bx,by=pos[b];aw,ah,*_=metrics[a];bw,bh,*_=metrics[b]
            if abs((ay+ah/2)-(by+bh/2))>max(ah,bh)*.52:
                return ('bottom','top') if ay<by else ('top','bottom')
            return ('right','left') if ax<bx else ('left','right')
        sides=[]
        for i,r in enumerate(relations):
            sa,sb=side_for(r['from'],r['to']);sides.append((sa,sb))
            side_links.setdefault((r['from'],sa),[]).append((i,r['to']))
            side_links.setdefault((r['to'],sb),[]).append((i,r['from']))
        offsets={}
        for key,items in side_links.items():
            items.sort(key=lambda item:(pos[item[1]][0]+metrics[item[1]][0]/2,pos[item[1]][1]+metrics[item[1]][1]/2))
            for j,(i,_) in enumerate(items):offsets[(i,key)]=(j+1)/(len(items)+1)
        def edgepoint(node,side,t):
            x,y=pos[node];cw,ch,*_=metrics[node]
            if side=='top':return (x+cw*(.15+.70*t),y)
            if side=='bottom':return (x+cw*(.15+.70*t),y+ch)
            if side=='left':return (x,y+ch*(.15+.70*t))
            return (x+cw,y+ch*(.15+.70*t))
        for i,r in enumerate(relations):
            a,b=r['from'],r['to'];sa,sb=sides[i]
            p=edgepoint(a,sa,offsets[(i,(a,sa))]);q=edgepoint(b,sb,offsets[(i,(b,sb))])
            points=r.get('clean_points',[p,q])
            s.routes.append({'from':a,'to':b,'points':points})
            s.line(points,arrow='filled',color='#34454c',sw=1.8)
        s.notes.append('此图为有向关联概览；关系种类和数量约束见源模型及正文表，箭头只表示本图阅读方向。')
        s.counts={'classes':len(cs),'attributes':sum(len(c.get('attributes',[])) for c in cs),'constructors_or_methods':sum(len(c.get('methods',[])) for c in cs),'generalizations':sum(len(v) for v in inherit.values()),'other_relations':len(relations)}
        return s
    semantic_sides=[];semantic_offsets={}
    if semantic:
        side_links={}
        for i,r in enumerate(m.get('relations',[])):
            a,b=r['from'],r['to'];ax,ay=pos[a];bx,by=pos[b];aw,ah,*_=metrics[a];bw,bh,*_=metrics[b]
            if ay+ah<=by:
                sa,sb='bottom','top'
            elif by+bh<=ay:
                sa,sb='top','bottom'
            elif ax+aw<=bx:
                sa,sb='right','left'
            else:
                sa,sb='left','right'
            sa=r.get('from_side',sa);sb=r.get('to_side',sb);semantic_sides.append((sa,sb))
            side_links.setdefault((a,sa),[]).append((i,b))
            side_links.setdefault((b,sb),[]).append((i,a))
        for key,items in side_links.items():
            items.sort(key=lambda item:(pos[item[1]][0]+metrics[item[1]][0]/2,pos[item[1]][1]+metrics[item[1]][1]/2))
            for j,(i,_) in enumerate(items):semantic_offsets[(i,key)]=(j+1)/(len(items)+1)
        def semantic_edgepoint(node,side,t):
            x,y=pos[node];cw,ch,*_=metrics[node]
            if side=='top':return (x+cw*(.12+.76*t),y)
            if side=='bottom':return (x+cw*(.12+.76*t),y+ch)
            if side=='left':return (x,y+ch*(.12+.76*t))
            return (x+cw,y+ch*(.12+.76*t))
    for i,r in enumerate(m.get('relations',[])):
        a,b=r['from'],r['to'];ax,ay=pos[a];bx,by=pos[b];aw,ah,*_=metrics[a];bw,bh,*_=metrics[b];kind=r.get('kind','association')
        if kind not in ['association','aggregation','composition','dependency','realization','generalization']:raise ValueError('未知类关系 '+kind)
        if semantic and not r.get('points'):
            sa,sb=semantic_sides[i];start=semantic_edgepoint(a,sa,semantic_offsets[(i,(a,sa))]);end=semantic_edgepoint(b,sb,semantic_offsets[(i,(b,sb))])
            if sa in ['top','bottom']:
                mid=(start[1]+end[1])/2;points=[start,(start[0],mid),(end[0],mid),end]
            else:
                mid=(start[0]+end[0])/2;points=[start,(mid,start[1]),(mid,end[1]),end]
        elif bx>=ax+aw:
            start,end=(ax+aw,ay+ah/2),(bx,by+bh/2);mid=(start[0]+end[0])/2;points=[start,(mid,start[1]),(mid,end[1]),end]
        elif ax>=bx+bw:
            start,end=(ax,ay+ah/2),(bx+bw,by+bh/2);mid=(start[0]+end[0])/2;points=[start,(mid,start[1]),(mid,end[1]),end]
        else:
            down=by>ay;start=(ax+aw/2,ay+ah if down else ay);end=(bx+bw/2,by if down else by+bh);mid=(start[1]+end[1])/2;points=[start,(start[0],mid),(end[0],mid),end]
        points=r.get('points',points)
        s.routes.append({'from':a,'to':b,'points':points})
        relation_color=m.get('relation_color','#303a43')
        s.line(points,arrow='open' if kind=='dependency' or r.get('navigable') else 'hollow' if kind in ['realization','generalization'] else None,dash=kind in ['dependency','realization'],color=relation_color,sw=m.get('relation_line_width',1.45 if semantic else 1))
        if kind in ['aggregation','composition']:
            # `from` owns the diamond; the path direction does not change ownership.
            x,y=points[0];nx,ny=points[1];angle=math.atan2(ny-y,nx-x);L,H=18,6
            q=[(x,y),(x+L/2*math.cos(angle)+H*math.sin(angle),y+L/2*math.sin(angle)-H*math.cos(angle)),(x+L*math.cos(angle),y+L*math.sin(angle)),(x+L/2*math.cos(angle)-H*math.sin(angle),y+L/2*math.sin(angle)+H*math.cos(angle))];s.polygon(q,fill=relation_color if kind=='composition' else 'white',stroke=relation_color,sw=m.get('relation_line_width',1.45 if semantic else 1))
        if r.get('label'):
            segments=list(zip(points,points[1:]));p1,p2=max(segments,key=lambda pair:math.hypot(pair[1][0]-pair[0][0],pair[1][1]-pair[0][1]))
            if abs(p2[0]-p1[0])<abs(p2[1]-p1[1]):
                automatic=[(p1[0]+p2[0])/2+48,(p1[1]+p2[1])/2-size*.45]
            else:
                automatic=[(p1[0]+p2[0])/2,(p1[1]+p2[1])/2-26]
            relation_label_size=r.get('label_font_size',m.get('relation_label_font_size',size*.8))
            lx,ly=r.get('label_position',automatic);s.text(lx,ly,r['label'],size=relation_label_size)
        for field,pt in [('from_multiplicity',points[0]),('to_multiplicity',points[-1])]:
            if r.get(field):
                other=points[1] if field.startswith('from') else points[-2]
                dx,dy=other[0]-pt[0],other[1]-pt[1];length=max(1,math.hypot(dx,dy));ux,uy=dx/length,dy/length;pxv,pyv=uy,-ux
                along=34 if field=='from_multiplicity' and kind in ['aggregation','composition'] else 21
                auto=[pt[0]+ux*along+pxv*14,pt[1]+uy*along+pyv*14-size*.45]
                px,py=r.get(field+'_position',auto);s.text(px,py,r[field],size=r.get('multiplicity_font_size',m.get('multiplicity_font_size',size*.75)),family='Arial')
    s.counts={'classes':len(cs),'attributes':sum(len(c.get('attributes',[])) for c in cs),'constructors_or_methods':sum(len(c.get('methods',[])) for c in cs),'generalizations':sum(len(v) for v in inherit.values()),'other_relations':len(m.get('relations',[]))};return s

def render_schema(m,st):
    ts=m['tables'];size=m.get('font_size',12);cols=m.get('columns',4);gap=35;head=27;row=19;positions={};cury=20;maxx=0
    for start in range(0,len(ts),cols):
        group=ts[start:start+cols];x=20;maxh=0
        for t in group:
            tw=t.get('width',max(175,max(measure(a['name']+': '+a['type'],size,'Arial')[0]+35 for a in t['fields'])));th=head+len(t['fields'])*row+12;tx,ty=t.get('position',[x,cury]);positions[t['id']]=(tx,ty,tw,th);x+=tw+gap;maxx=max(maxx,tx+tw);maxh=max(maxh,th)
        cury+=maxh+gap
    w=m.get('width',maxx+20);h=m.get('height',max(y+th for x,y,tw,th in positions.values())+20);s=Scene(w,h,st)
    if m.get('grid',True):
        for x in range(0,int(w),10):s.line([(x,0),(x,h)],color='#f4f4f4',sw=.5)
        for y in range(0,int(h),10):s.line([(0,y),(w,y)],color='#f4f4f4',sw=.5)
    for t in ts:
        x,y,tw,th=positions[t['id']];s.rect(x,y,tw,th,rx=9,stroke='#5184b0');s.rect(x,y,tw,head,rx=7,fill='#5184b0',stroke='#5184b0');s.rect(x,y+head-8,tw,8,fill='#5184b0',stroke='#5184b0');s.text(x+tw/2,y+7,t['name'],size=size,family='Arial',bold=True,color='white',container=[x+5,y+2,x+tw-5,y+head-2])
        for i,a in enumerate(t['fields']):
            yy=y+head+i*row+6;off=12
            if a.get('pk'):
                s.ellipse(x+12,yy+4,3,3,fill='#f1d45a',stroke='#c4ad4b');s.line([(x+10,yy+6),(x+6,yy+11),(x+4,yy+9)],color='#c4ad4b',sw=2);off=25
            text=a['name']+': '+a['type'];s.text(x+off,yy,text,size=size,family='Arial',anchor='start',container=[x+3,y+head,x+tw-3,y+th-3])
        s.box(t['id'],x,y,tw,th)
    for r in m.get('relations',[]):
        a=positions[r['from']];b=positions[r['to']];ps=r.get('points',[(a[0]+a[2],a[1]+a[3]/2),(b[0],b[1]+b[3]/2)]);s.line(ps,color='#5184b0',arrow='open');
    s.counts={'tables':len(ts),'fields':sum(len(t['fields']) for t in ts),'relations':len(m.get('relations',[]))};return s

def render_layered(m,st):
    size=m.get('font_size',14);w=m.get('width',900);top=110;logic=360;h=m.get('height',600);s=Scene(w,h,st);s.rect(1,1,w-2,h-2,stroke='#777777');s.line([(1,top),(w-1,top)],color='#777777');s.line([(1,top+logic),(w-1,top+logic)],color='#777777');s.text(22,40,'表现层',size=size+3,bold=True,anchor='start');s.text(22,top+logic/2-10,'逻辑层',size=size+3,bold=True,anchor='start');s.text(22,top+logic+50,'数据层',size=size+3,bold=True,anchor='start')
    left=125;right=w-25;roles=m['roles'];rw=min(160,(right-left)/len(roles)-30)
    for i,r in enumerate(roles):
        x=left+(right-left)*(i+.5)/len(roles)-rw/2;s.rect(x,35,rw,40,rx=6,stroke='#777777');s.text(x+rw/2,48,r,size=size,container=[x+6,36,x+rw-6,74])
    common=m.get('common',[])
    for i,l in enumerate(common):
        cw=(right-left)/max(1,len(common))-25;x=left+i*(right-left)/len(common);s.rect(x,top+35,cw,42,stroke='#777777');s.text(x+cw/2,top+49,l,size=size,container=[x+5,top+36,x+cw-5,top+76])
    groups=m['groups'];gw=(right-left)/len(groups)-15
    maxn=max(len(g['items']) for g in groups);gh=maxn*54+60
    if gh>logic-125:raise ValueError('逻辑层项目过多。增大 render_layered 中 logic 高度或拆分分组图，不要缩小字到难以阅读。')
    for i,g in enumerate(groups):
        x=left+i*(right-left)/len(groups);y=top+110;s.rect(x,y,gw,gh,stroke='#777777',dash=True);s.text(x+gw/2,y+17,g['label'],size=size)
        for j,l in enumerate(g['items']):s.rect(x+10,y+55+j*54,gw-20,38,stroke='#777777');s.text(x+gw/2,y+67+j*54,l,size=size,container=[x+15,y+56+j*54,x+gw-15,y+92+j*54])
    x=w/2;yy=top+logic+45;s.rect(x-80,yy,160,40,stroke='#777777');s.ellipse(x,yy,80,10,stroke='#777777');s.text(x,yy+15,m.get('database','MySQL'),size=size,family='Arial');s.counts={'roles':len(roles),'common_modules':len(common),'groups':len(groups),'modules':sum(len(g['items']) for g in groups)};return s

def render_tree(m,st):
    nodes=m['nodes'];size=m.get('font_size',18);gap=m.get('leaf_gap',22);nw=m.get('node_width',52);rh=m.get('root_height',70);level=m.get('level_gap',250);vertical=m.get('vertical',True);root=nodes[0];children={n['id']:[] for n in nodes}
    lookup={n['id']:n for n in nodes}
    for n in nodes[1:]:children[n['parent']].append(n['id'])
    count={}
    def leaves(id):
        if id in count:return count[id]
        count[id]=sum(leaves(c) for c in children[id]) if children[id] else 1;return count[id]
    leaves(root['id']);w=m.get('width',max(720,40+count[root['id']]*(nw+gap)));depths={root['id']:0};centers={}
    def place(id,left,right):
        centers[id]=(left+right)/2;cur=left
        for c in children[id]:
            span=(right-left)*count[c]/count[id];depths[c]=depths[id]+1;place(c,cur,cur+span);cur+=span
    place(root['id'],25,w-25);maxdepth=max(depths.values());h=m.get('height',maxdepth*level+420);s=Scene(w,h,st);positions={}
    for n in nodes:
        d=depths[n['id']];x=centers[n['id']];y=25+d*level
        if not d:ww=max(300,measure(n['label'],size,st['font'])[0]+35);hh=rh;text=n['label']
        else:
            ww=n.get('width',nw);text='\n'.join(n['label']) if vertical else wrap(n['label'],ww-15,size,st['font']);hh=n.get('height',max(160,len(text.split('\n'))*size*1.5+24))
        positions[n['id']]=(x-ww/2,y,ww,hh,text)
    for parent,kids in children.items():
        if not kids:continue
        px,py,pw,ph,_=positions[parent];x=px+pw/2;bus=max(py+ph+25,min(positions[k][1] for k in kids)-45);xx=[centers[k] for k in kids];s.line([(x,py+ph),(x,bus)],sw=1.5);s.line([(min(xx),bus),(max(xx),bus)],sw=1.5)
        for kid in kids:s.line([(centers[kid],bus),(centers[kid],positions[kid][1])],sw=1.5)
    for n in nodes:
        x,y,ww,hh,text=positions[n['id']];s.rect(x,y,ww,hh,sw=1.5);lh=len(text.split('\n'))*size*1.25;s.text(x+ww/2,y+(hh-lh)/2+3,text,size=size,container=[x+3,y+3,x+ww-3,y+hh-3]);s.box(n['id'],x,y,ww,hh)
    s.counts={'nodes':len(nodes),'hierarchy_edges':len(nodes)-1};return s

def render_deployment(m,st):
    """Measured five-stage topology; icon silhouettes are deterministic approximations."""
    stages=m['stages'];w=m.get('width',1100);h=m.get('height',500);s=Scene(w,h,st);xs=[135,385,600,780,975];ys={};stagepoints={}
    for i,g in enumerate(stages):
        x=g.get('x',xs[i] if i<5 else 100+i*180);count=g.get('count',1);rows=[220] if count==1 else [120,300] if count==2 else [100+j*130 for j in range(count)];stagepoints[g['id']]=[(x,y) for y in rows];ys[g['id']]=rows
    for edge in m['edges']:
        aa=stagepoints[edge['from']];bb=stagepoints[edge['to']]
        pairs=list(zip(aa,bb)) if len(aa)==len(bb) else [(a,b) for a in aa for b in bb]
        for a,b in pairs:s.line([(a[0]+46,a[1]),(b[0]-46,b[1])],arrow='open',color='#28303d',sw=2)
    for g in stages:
        for x,y in stagepoints[g['id']]:
            k=g.get('kind','server')
            if k=='client':
                s.rect(x-40,y-22,57,43,fill='#d3f0ef',stroke='#26343e',sw=2);s.rect(x-15,y+21,8,8,fill='#adbec9',stroke='none');s.line([(x-24,y+30),(x-2,y+30)],color='#adbec9',sw=3);s.rect(x+24,y-34,24,64,fill='#26343e');
                for j in range(6):s.line([(x+28,y-28+j*6),(x+43,y-28+j*6)],color='#aabaca')
            elif k=='internet':
                for dx,dy,r in [(-20,0,22),(0,-18,25),(21,-9,23),(28,9,15)]:s.ellipse(x+dx,y+dy,r,r,fill='#58bec3',stroke='none')
                s.ellipse(x+4,y+7,18,18,fill='#dce1e4',stroke='#42475d',sw=5);s.line([(x+16,y+22),(x+36,y+43)],sw=6,color='#42475d')
            elif k=='database':
                s.rect(x-28,y-24,55,48,fill='white',stroke='#28303d',sw=3)
                for j in range(4):s.ellipse(x,y-24+j*14,28,8,stroke='#28303d',sw=3)
            else:
                for j in range(3):
                    yy=y-40+j*25;s.rect(x-42,yy,84,20,fill='#35424a',rx=3,stroke='#25333b',sw=2)
                    for gx in range(6):
                        for gy in range(2):s.rect(x-36+gx*7,yy+5+gy*6,4,2,fill='#dedb4c',stroke='none')
                    s.ellipse(x+26,yy+10,4,4,fill='#82959f',stroke='none')
                s.line([(x,y+27),(x,y+35)],color='#aabdc6',sw=4);s.line([(x-28,y+35),(x+28,y+35)],color='#aabdc6',sw=3)
            if g.get('technology'):s.text(x,y+57,g['technology'],size=16,family='Arial')
        s.text(stagepoints[g['id']][0][0],h-64,g['label'],size=23)
    s.notes.append('服务器、终端、云和数据库图标是矢量轮廓近似；不是原稿图标的像素级复刻。');s.counts={'stages':len(stages),'nodes':sum(len(v) for v in stagepoints.values()),'topology_edges':sum(len(stagepoints[e['from']])*len(stagepoints[e['to']]) if len(stagepoints[e['from']])!=len(stagepoints[e['to']]) else len(stagepoints[e['from']]) for e in m['edges'])};return s

RENDERERS={'usecase':render_usecase,'sequence':render_sequence,'bce':render_bce,'class':render_classes,'schema':render_schema,'layered':render_layered,'tree':render_tree,'deployment':render_deployment}
def validate_model(m):
    if m.get('type') not in RENDERERS:raise ValueError('type 必须为 '+', '.join(RENDERERS))
    if m.get('profile','mayuyang') not in PROFILES:raise ValueError('未知 profile')
    typ=m['type'];key={'usecase':'usecases','sequence':'participants','class':'classes','schema':'tables','tree':'nodes'}.get(typ)
    if key:
        ids=[a['id'] for a in m[key]]
        if len(ids)!=len(set(ids)):raise ValueError('重复的节点 id')
    if typ=='usecase':
        actors={a['id'] for a in m['actors']}
        for u in m[key]:
            if set(u.get('actors',[]))-actors:raise ValueError('用例引用了不存在的角色')
    if typ in ['sequence','class','schema','usecase']:
        entries=m.get('messages',[]) if typ=='sequence' else m.get('relations',[])
        for e in entries:
            if e['from'] not in ids or e['to'] not in ids:raise ValueError('关系引用了不存在的节点')
    if typ=='sequence':
        for e in m['messages']:
            if e.get('kind','call') not in ('call','return','async'):raise ValueError('未知序列消息类型')
        for f in m.get('fragments',[]):
            if f['start']<0 or f['end']>=len(m['messages']) or f['end']<f['start']:raise ValueError('片段范围不合法')
            if f.get('from') not in ids or f.get('to') not in ids:raise ValueError('片段生命线不存在')
            if f.get('operator','alt') not in ('alt','opt','loop'):raise ValueError('未知组合片段类型')
            starts=[op.get('start') for op in f.get('operands',[])]
            if starts and (starts[0]!=f['start'] or starts!=sorted(set(starts)) or starts[-1]>f['end']):raise ValueError('分支起点必须按顺序位于片段内')
            if any(not op.get('guard') for op in f.get('operands',[])):raise ValueError('分支条件不能为空')
        for a in m.get('activations',[]):
            if a.get('participant') not in ids:raise ValueError('激活条参与者不存在')
            if 'start_message' in a:
                first,last=a['start_message'],a.get('end_message',a['start_message'])
                if not (isinstance(first,int) and isinstance(last,int) and 0<=first<=last<len(m['messages'])):
                    raise ValueError('激活条消息索引不合法')
            elif a.get('end',0)<=a.get('y',0):raise ValueError('激活条区间不合法')
    if typ=='class':
        parents={c['id']:c.get('parent') for c in m[key]}
        for c in m[key]:
            if c.get('parent') and c['parent'] not in ids:raise ValueError('父类不存在')
            visited=set();cur=c['id']
            while cur:
                if cur in visited:raise ValueError('继承关系存在循环')
                visited.add(cur);cur=parents.get(cur)
    if typ=='tree':
        if len(m['nodes'])!=len(set(ids)):raise ValueError('树节点重复')
        parents={n['id']:n.get('parent') for n in m['nodes']}
        for n in m['nodes'][1:]:
            visited=set();cur=n['id']
            while cur is not None:
                if cur in visited:raise ValueError('层次树存在循环')
                if cur not in parents:raise ValueError('层次树父节点不存在')
                visited.add(cur);cur=parents[cur]

def render_file(modelpath,outdir,scale=3,strict=False):
    m=json.loads(Path(modelpath).read_text(encoding='utf-8-sig'));validate_model(m);st={**PROFILES[m.get('profile','mayuyang')]};scene=RENDERERS[m['type']](m,st);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True);name=Path(modelpath).stem
    audit=scene.audit();audit['model']=name;audit['source_trace']=m.get('source_trace',False)
    save_svg(scene,outdir/(name+'.svg'));save_png(scene,outdir/(name+'.png'),scale);save_drawio(scene,outdir/(name+'.drawio'));save_plantuml(m,outdir/(name+'.puml'))
    (outdir/(name+'.scene.json')).write_text(json.dumps({'width':scene.w,'height':scene.h,'ops':scene.ops},ensure_ascii=False,indent=2),encoding='utf8', newline='\n')
    (outdir/(name+'.audit.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8', newline='\n')
    if strict and audit['issues']:raise RuntimeError(f'{name}: {len(audit["issues"])} 个布局问题，查看 audit.json 并修正。')
    return audit
def main():
    global FONT_OVERRIDE
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',help='JSON 文件或含 JSON 模型的目录');parser.add_argument('--out',required=True);parser.add_argument('--scale',type=float,default=3);parser.add_argument('--font');parser.add_argument('--strict',action='store_true');a=parser.parse_args();FONT_OVERRIDE=a.font
    if a.scale<1:parser.error('--scale 至少为 1')
    src=Path(a.model);files=sorted(src.glob('*.json')) if src.is_dir() else [src]
    if not files:parser.error('没有找到 JSON 模型')
    for file in files:
        r=render_file(file,a.out,a.scale,a.strict);print(json.dumps({'model':file.name,'counts':r['counts'],'layout_issues':len(r['issues'])},ensure_ascii=False))
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')
    main()
