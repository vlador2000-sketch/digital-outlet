from __future__ import annotations
import base64, html as htmllib, io, re, time, unicodedata
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image, ImageOps
from ddgs import DDGS

HTML=Path('DiGiTaL.html'); OUT=Path('covers'); OUT.mkdir(exist_ok=True)
raw=HTML.read_text(encoding='utf-8')
card_re=re.compile(r'<article class="card">.*?</article>',re.S)
cards=card_re.findall(raw)
if len(cards)!=86: raise SystemExit(f'ABORT: expected 86 cards, found {len(cards)}')

ALIASES={
'A Plague Tale: Innocence':'A Plague Tale Innocence PS4',
'Car for Sale Simulator 2023':'Car For Sale Simulator 2023 game cover',
'Crash Team Rumble':'Crash Team Rumble PS5',
'Darksiders Fury’s Collection':"Darksiders Fury's Collection War and Death PS4",
'ELDEN RING':'Elden Ring PS4 PS5',
'Hogwarts Legacy':'Hogwarts Legacy PS5',
'Holdfast: Nations At War':'Holdfast Nations At War PS5',
'PAYDAY 2':'PAYDAY 2 Crimewave Edition PS4',
'Ratchet & Clank: Rift Apart':'Ratchet Clank Rift Apart PS5',
'Rayman Legends':'Rayman Legends PS4',
'Subnautica: Below Zero':'Subnautica Below Zero PS4 PS5',
'TABS: Totally Accurate Battle Simulator':'Totally Accurate Battle Simulator PS4 PS5',
'Unravel Yarny Bundle':'Unravel Yarny Bundle PS4',
'Watch Dogs 2':'Watch Dogs 2 PS4',
'GOD OF WAR III':'God of War III Remastered PS4',
'Spyro':'Spyro Reignited Trilogy PS4',
'Metal Slug 3':'Metal Slug 3 PS4',
'Project CARS 2':'Project CARS 2 PS4',
'UNCHARTED 4':"Uncharted 4 A Thief's End PS4",
'F1 2020':'F1 2020 PS4',
'Rainbow Six':"Tom Clancy's Rainbow Six Siege PS4",
'AO International Tennis':'AO International Tennis PS4',
'Wolfenstein Youngblood':'Wolfenstein Youngblood PS4',
'GTA V - PS4':'Grand Theft Auto V PS4',
'Marvel’s Avengers':"Marvel's Avengers PS4",
'SCARF':'SCARF game PS4',
'AO Tennis 2':'AO Tennis 2 PS4'
}

# Confirmed high-resolution sources from official PlayStation pages / CDN where possible.
KNOWN={
'A Plague Tale: Innocence':'https://image.api.playstation.com/vulcan/ap/rnd/202106/2216/ZAIadbeOcklw9LD0PQKUzIcJ.jpg',
'PAYDAY 2':'https://image.api.playstation.com/vulcan/ap/rnd/202409/1918/87fdbc9a74abe03fe9cf581b8e1fcb3e356ce1f7426d4593.jpg',
'Spyro':'https://image.api.playstation.com/cdn/UP0002/CUSA12125_00/wQimEr4XlJnBh9zJL6h8vwIoB919zvRy.png',
'Unravel Yarny Bundle':'https://image.api.playstation.com/vulcan/img/rnd/202010/1520/Zn6JKFaqhuWXqqehxCqkXarQ.jpg',
'Metal Slug 3':'https://image.api.playstation.com/vulcan/img/rnd/202010/2621/SXzudkevxT3axdKCevklCxP6.png',
'ELDEN RING':'https://image.api.playstation.com/vulcan/ap/rnd/202110/2000/YMUoJUYNX0xWk6eTKuZLr5Iw.jpg',
'Ratchet & Clank: Rift Apart':'https://image.api.playstation.com/vulcan/ap/rnd/202101/2921/U0nZxiIiAGP67E0j94AJNmYb.jpg',
'Darksiders III: Blades & Whip':'https://image.api.playstation.com/vulcan/img/rnd/202010/3012/hfGD6MxHeVzXDRgFjVkwBEt7.png',
'DYNASTY WARRIORS 9':'https://image.api.playstation.com/vulcan/img/cfn/11307UathmM4W46n57PareHILzlRE5ddBcJO4cOoFwkJkOR8cewaTMTgsvq7wPZ2OyKKyAJmVlYE3r5JTMi0V8HT9jM4Jzrc.png',
'F1 25':'https://image.api.playstation.com/vulcan/ap/rnd/202507/0312/476d59c00f9617db09ca982d75ad0a3d15e755aeaa456b67.png',
'Farming Simulator 25':'https://image.api.playstation.com/vulcan/ap/rnd/202511/0613/3d526a8a4cb5d57a094d0f53a352551464c46442d9944a53.png',
'Journey':'https://image.api.playstation.com/vulcan/img/rnd/202010/2917/Cj8ngIRc3MB1uhNR40BQhzXv.png',
'King’s Bounty II: Lord’s Edition':'https://image.api.playstation.com/vulcan/ap/rnd/202105/1217/Kf2m9rFXExaSBhwp9YsMai12.png',
'LEGO Star Wars: The Skywalker Saga':'https://image.api.playstation.com/vulcan/ap/rnd/202210/1822/Fb4ELiu7ufj8pEVu9Zdcttmv.png',
'NHL 25':'https://image.api.playstation.com/vulcan/ap/rnd/202508/2700/6314579aed75a3b1020af332be9e599f9f1bf08db88bd4dc.png',
'Outlast 2':'https://image.api.playstation.com/vulcan/coal-image-prod/cdn/molt/ALL/201905/MOLT2276_ZZ/rUhQGewc1LDM3PMCNg.png',
'Pathologic 2':'https://image.api.playstation.com/vulcan/img/cfn/11307rpucdi-vJW6obElslbuBM4_MCv3RQ84yop8-wejoLa0IqokIRkb_sZLKYwry0x6XKTpcgd2izaX9Y1-wDZUlfcBh41r.png',
'Police Simulator: Patrol Officers':'https://image.api.playstation.com/vulcan/ap/rnd/202509/1514/465bca1e8f6e38b2b23fe1db4f1d3e0da5251edbf01d1c91.png',
'STAR WARS Episode I: Racer':'https://image.api.playstation.com/vulcan/ap/rnd/202006/1021/7MVAn1rcsLnGveDjJJs1eYcH.png',
'Suicide Guy':'https://image.api.playstation.com/vulcan/ap/rnd/202311/1016/d97c43dfb356736124171966f034e07050af48957f392d36.png',
'UFC 3':'https://image.api.playstation.com/vulcan/ap/rnd/202310/2321/36d14d29566625d28920111d83c83dbb7e9fc8b1f1cee20a.png',
'Forza Horizon 5':'https://image.api.playstation.com/vulcan/ap/rnd/202506/1017/6dd6f52046d86937817680887cd06b99cfde9f427dee418f.png',
'NBA 2K26':'https://image.api.playstation.com/vulcan/ap/rnd/202602/2723/0a50afa4eb1f9d5bb32a421431003e6452311e3af311b2d3.png',
'WRC 7':'https://image.api.playstation.com/cdn/EP4008/CUSA08226_00/ofxBmUYRZR5kFaD5b3nLPvhIl1KvM6vf.png',
'WRC 9':'https://image.api.playstation.com/vulcan/ap/rnd/202409/2522/206c27c9cdc627372195e75bd4fe393d23f35d3c4737940d.png',
'Mafia III':'https://image.api.playstation.com/cdn/UP1001/CUSA03652_00/eIuxZXIU8vTGYeLSgyJfG4GLbN9upeg6SMfTtilLiyEUZSdOmcsJ4gDETehQh7BT.png',
'Miles Morales':'https://image.api.playstation.com/vulcan/ap/rnd/202008/1020/T45iRN1bhiWcJUzST6UFGBvO.png',
'MOTO GP 19':'https://image.api.playstation.com/cdn/UP1981/CUSA14888_00/fc8j4ga8D7TslO3M1inw8dOV9WnTnK8G.png',
'MotoGP 20':'https://image.api.playstation.com/vulcan/img/cfn/11307twyLBi9bBOqgootgZVFpJQSGx-8POPNJ0Nk4iupFSDIFpXcAZKgdDDtz4w33Whh2Ac5a2OpmpQZFYJTODunSpUXNRRk.png',
'GRAN TURISMO':'https://image.api.playstation.com/vulcan/ap/rnd/202411/2507/f3e188254bee44e60aca10a86ce9184293fa24ba169e9249.png',
'Farming Simulator 19':'https://image.api.playstation.com/vulcan/img/cfn/11307LG7i_ZMXH-XoCW7eBck3iAPop6g9snYOeUsAJps9dgo_jaLERg5BiJ27rA1sPRFhPEn8dnbYvRFJ3KEXHwrNsMkb69T.png',
'The Sims 4':'https://image.api.playstation.com/vulcan/ap/rnd/202409/0421/7187106e136e95e64c67a60e2301aad83c88e5a1e4a7324d.png',
'WORMS':'https://image.api.playstation.com/vulcan/ap/rnd/202407/0312/7332b03da43ba775a707dec4e0b28166ea11f580f52b1f76.png',
'Sniper Elite 4':'https://image.api.playstation.com/vulcan/ap/rnd/202503/0715/c6681a0fa442d5ed31bf35bf86fde59872a81b965c41e883.png',
'Sniper Remastered':'https://image.api.playstation.com/vulcan/ap/rnd/202504/1113/24fa184183349615600fabdb7907ac752271fdb1e73f0944.png',
'GHOST BREAKPOINT':'https://image.api.playstation.com/vulcan/img/rnd/202109/0713/w2VGFO3HIVX4YZ4DwQuQ416V.png',
'Devil May Cry':'https://image.api.playstation.com/vulcan/ap/rnd/202009/1710/UUnpHLJqLAIJX5HioswiPuAm.png',
'MudRunner - American Wilds Edition':'https://image.api.playstation.com/cdn/UP4133/CUSA09936_00/IIZ87B93JkyGaSA3XMzqd0hmTaQXZdeX.png',
'THIEF':'https://image.api.playstation.com/cdn/UP0082/CUSA00252_00/Ew3YZN6CUmRZlDq38bvQLZNAfLpXIC0G.png',
'Little Nightmares II':'https://image.api.playstation.com/vulcan/ap/rnd/202204/1908/pam5dUS6w13ovToXCy8mcRZ6.png',
'Shadow of the Tomb Raider':'https://image.api.playstation.com/vulcan/img/cfn/11307kGDEQ-Af4VjkwzfffuEE2DIn5-r1kMp86kg5PyUc7morSMv04cMbucnKivYNnLJl5Y11Ys7pXuLan1YW7zg1XsxKtb0.png',
"Five Nights at Freddy's Security Breach":'https://image.api.playstation.com/vulcan/img/rnd/202112/0804/2UTMvRFqn4SdaoxhtQnxchcn.png',
'Mortal Kombat 11':'https://image.api.playstation.com/vulcan/ap/rnd/202305/1515/1cc63f4f4b2c9a9852fabefba4ca7eea936b1ef7867811a5.png'
}

session=requests.Session(); session.headers.update({'User-Agent':'Mozilla/5.0 Chrome/139 Safari/537.36','Accept':'image/avif,image/webp,image/*,*/*;q=0.8'})

def text_between(block,cls):
 m=re.search(rf'<div class="{re.escape(cls)}">(.*?)</div>',block,re.S); return htmllib.unescape(re.sub('<[^>]+>','',m.group(1)).strip()) if m else ''
def get_src(block):
 m=re.search(r'<img[^>]*class="cover"[^>]*src="([^"]+)"',block,re.S) or re.search(r'<img[^>]*src="([^"]+)"[^>]*class="cover"',block,re.S); return htmllib.unescape(m.group(1)) if m else ''
def safe_slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:72] or 'cover'
def get_bytes(src):
 if not src:return None
 if src.startswith('data:image/'):
  try:return base64.b64decode(src.split(',',1)[1])
  except:return None
 if src.startswith(('http://','https://')):
  try:
   r=session.get(src,timeout=18,allow_redirects=True); return r.content if r.ok and len(r.content)>1000 else None
  except:return None
 p=Path(src.lstrip('/')) if src.startswith('/') else Path(src)
 return p.read_bytes() if p.exists() else None
def info(data):
 if not data:return None
 try:
  with Image.open(io.BytesIO(data)) as im: im.load(); return im.width,im.height,im.format
 except:return None

def tokens(s):
 stop={'ps4','ps5','the','and','of','edition','collection','bundle','game','for','a','an','remastered','standard'}
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); return [x for x in re.findall(r'[a-z0-9]+',s) if len(x)>1 and x not in stop]
def match_score(title,meta):
 alias=ALIASES.get(title,title); t=tokens(alias); m=unicodedata.normalize('NFKD',meta or '').encode('ascii','ignore').decode().lower(); return sum(x in m for x in t)/max(1,len(t))
def candidate(url):
 try:
  r=session.get(url,timeout=15,allow_redirects=True,stream=True)
  if not r.ok:return None
  d=r.raw.read(12_000_001); return d if 3000<len(d)<=12_000_000 else None
 except:return None

def find_best(title):
 if title in KNOWN:
  d=candidate(KNOWN[title]); ii=info(d)
  if ii and ii[0]>=650 and ii[1]>=650:return d,KNOWN[title],ii,'confirmed'
 alias=ALIASES.get(title,title)
 qs=[f'"{alias}" PlayStation cover',f'"{alias}" cover art',f'{alias} PlayStation Store',f'{alias} game cover']
 res=[]
 try:
  dd=DDGS()
  for q in qs:
   try:
    for r in dd.images(q,max_results=35):
     u=r.get('image') or ''
     if not u.startswith('http'):continue
     dom=urlparse(u).netloc.lower(); meta=' '.join([r.get('title') or '',r.get('url') or '',u]); ms=match_score(title,meta)
     if ms<0.38:continue
     if any(x in dom for x in ['wallpapers.com','pinterest.','pinimg.']):continue
     bonus=120 if 'image.api.playstation.com' in dom else 75 if ('playstation.com' in dom or 'gmedia.playstation.com' in dom) else 35 if any(x in dom for x in ['ea.com','ubisoft.com','rockstargames.com','bandainamcoent.com','capcom.com','2k.com','bethesda.net','square-enix.com','sega.com','warnerbrosgames.com','epicgames.com','focus-entmt.com','steamstatic.com','akamaihd.net']) else 0
     res.append((bonus+ms*50,u))
   except Exception as e: print('SEARCH WARN',title,type(e).__name__,str(e)[:100])
 except Exception as e: print('SEARCH INIT WARN',title,e)
 seen=set(); best=None
 for base,u in sorted(res,reverse=True):
  if u in seen:continue
  seen.add(u); d=candidate(u); ii=info(d)
  if not ii:continue
  w,h,_=ii
  if w<600 or h<600:continue
  ratio=w/h
  if not (0.52<=ratio<=1.10):continue
  sc=base+(28 if 0.58<=ratio<=0.85 else 10)+min(w*h/1_000_000,8)
  if best is None or sc>best[0]:best=(sc,d,u,ii)
  if sc>=155:break
 if best:return best[1],best[2],best[3],'search'
 return None

sig_before=[(text_between(c,'game'),text_between(c,'price')) for c in cards]
rows=[]; unresolved=[]; new_cards=[]; used=set(); total_after=0; total_emb=0
for i,block in enumerate(cards,1):
 title=text_between(block,'game') or f'Game {i}'; price=text_between(block,'price'); src=get_src(block); original=get_bytes(src); ii=info(original); ow,oh=(ii[0],ii[1]) if ii else (0,0)
 if src.startswith('data:image/') and original:total_emb+=len(original)
 low=(not ii) or ow<380 or oh<480
 chosen=original; chosen_url=src; action='compressed original'
 if low:
  found=find_best(title)
  if found:
   chosen,chosen_url,ni,kind=found; action='replaced low-res source'; print(f'REPLACED: {title}: {ow}x{oh} -> {ni[0]}x{ni[1]} | {chosen_url}')
  else:
   unresolved.append((title,f'no high-res replacement; original {ow}x{oh}')); new_cards.append(block); continue
 if not chosen:
  found=find_best(title)
  if found:chosen,chosen_url,ni,kind=found; action='replaced unavailable source'
  else:unresolved.append((title,'unavailable')); new_cards.append(block); continue
 try:
  with Image.open(io.BytesIO(chosen)) as im:
   im=ImageOps.exif_transpose(im)
   if im.mode not in ('RGB','RGBA'):im=im.convert('RGB')
   if im.mode=='RGBA':
    bg=Image.new('RGB',im.size,'white'); bg.paste(im,mask=im.getchannel('A')); im=bg
   if im.width>420 or im.height>680:im.thumbnail((420,680),Image.Resampling.LANCZOS)
   q=70; out=io.BytesIO(); im.save(out,'WEBP',quality=q,method=6,optimize=True)
   while out.tell()>58_000 and q>52:
    q-=3; out=io.BytesIO(); im.save(out,'WEBP',quality=q,method=6,optimize=True)
   if out.tell()>70_000 and im.width>360:
    scale=360/im.width; im=im.resize((360,max(1,round(im.height*scale))),Image.Resampling.LANCZOS); q=60; out=io.BytesIO(); im.save(out,'WEBP',quality=q,method=6,optimize=True)
   data=out.getvalue(); nw,nh=im.size
 except Exception as e:
  unresolved.append((title,f'encode failed {e}')); new_cards.append(block); continue
 slug=safe_slug(title); base=slug; n=2
 while slug in used:slug=f'{base}-{n}';n+=1
 used.add(slug); rel=f'covers/{slug}.webp'; Path(rel).write_bytes(data); total_after+=len(data); new_src='/'+rel
 if src:
  repl=block.replace(f'src="{src.replace("&","&amp;")}"',f'src="{new_src}"',1)
  if repl==block:repl=block.replace(f'src="{src}"',f'src="{new_src}"',1)
 else:
  # A card missing a src: inject into its cover img if present, otherwise fail safely.
  repl=re.sub(r'(<img\b[^>]*class="cover"[^>]*)(>)',rf'\1 src="{new_src}"\2',block,count=1)
 if repl==block:
  unresolved.append((title,'src rewrite failed')); new_cards.append(block); continue
 new_cards.append(repl); rows.append({'game':title,'before':f'{ow}x{oh}' if ii else 'unavailable','after':f'{nw}x{nh}','bytes':len(data),'action':action,'source':chosen_url}); time.sleep(.03)

if unresolved:
 print('\nUNRESOLVED:'); [print(' -',t,why) for t,why in unresolved]; print(f'Resolved {len(rows)}/86, unresolved {len(unresolved)}'); raise SystemExit(2)
it=iter(new_cards); rewritten=card_re.sub(lambda m:next(it),raw); out_cards=card_re.findall(rewritten); sig_after=[(text_between(c,'game'),text_between(c,'price')) for c in out_cards]
if sig_after!=sig_before or len(out_cards)!=86:raise SystemExit('ABORT: catalog structure/content changed')
if 'data:image/' in ''.join(out_cards):raise SystemExit('ABORT: embedded cover data remains')
HTML.write_text(rewritten,encoding='utf-8')
before=len(raw.encode()); after=len(rewritten.encode()); report=Path('cover-optimization-report.md')
with report.open('w',encoding='utf-8') as f:
 f.write('# Catalog cover optimization report\n\n'); f.write(f'- Cards: 86\n- HTML before: {before:,} bytes\n- HTML after: {after:,} bytes\n- Optimized cover files: {len(rows)}\n- Total optimized cover bytes: {total_after:,}\n- Embedded image bytes removed (decoded): {total_emb:,}\n\n'); f.write('| Game | Before | After | WebP | Action | Source |\n|---|---:|---:|---:|---|---|\n')
 for r in rows:f.write(f"| {r['game'].replace('|','/')} | {r['before']} | {r['after']} | {r['bytes']/1024:.1f} KB | {r['action']} | {r['source']} |\n")
print(f'OK: 86/86 covers optimized; HTML {before:,}->{after:,}; covers {total_after:,} bytes')
