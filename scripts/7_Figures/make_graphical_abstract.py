# Graphical abstract, 2656 x 1062 px (twice the journal minimum of 1328 x 531 px), composed with PIL.
# Run after make_relettered_maps.py, which writes output/Fig18.pdf (FSIVI map used for the thumbnail).
from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm
W,H=2656,1062
img=Image.new("RGB",(W,H),"white")
d=ImageDraw.Draw(img)
def font(sz,bold=False,italic=False):
    from matplotlib import get_data_path
    import os
    base=os.path.join(get_data_path(),"fonts","ttf")
    f="DejaVuSans-Bold.ttf" if bold else ("DejaVuSans-Oblique.ttf" if italic else "DejaVuSans.ttf")
    return ImageFont.truetype(os.path.join(base,f), sz)
AZUL=(31,63,102); CINZA=(90,100,110); VERDE=(20,105,60); BORDA=(180,190,200)

# title
d.text((60,36),"Urban flood susceptibility without verified non-flood labels",font=font(56,bold=True),fill=AZUL)
d.text((60,110),"A reproducible Positive-and-Unlabeled learning framework — Paragominas, Brazilian Amazon",font=font(38),fill=CINZA)

# ---- panel 1: problem
x0,y0,x1,y1=60,200,820,960
d.rounded_rectangle([x0,y0,x1,y1],radius=18,outline=BORDA,width=4)
d.text((x0+30,y0+24),"Scarce labels",font=font(44,bold=True),fill=AZUL)
d.text((x0+30,y0+90),"2,280 samples inside official\nCPRM/SGB flood-risk sectors\n\nNo verified non-flood\nsamples at all",font=font(36),fill=(30,30,30))
# illustrative scatter: positives (blue) and unlabeled (grey)
import random
random.seed(7)
for i in range(60):
    px=random.randint(x0+60,x1-60); py=random.randint(y0+340,y1-120)
    if i<14: d.ellipse([px-13,py-13,px+13,py+13],fill=(40,90,160))
    else: d.ellipse([px-11,py-11,px+11,py+11],outline=(150,155,165),width=4)
d.ellipse([x0+32,y1-80,x0+56,y1-56],fill=(40,90,160)); d.text((x0+66,y1-90),"flood (P)",font=font(34),fill=CINZA)
d.ellipse([x0+262,y1-79,x0+284,y1-57],outline=(150,155,165),width=4); d.text((x0+294,y1-90),"unlabeled (U)",font=font(34),fill=CINZA)

# ---- arrow 1 (same shape as arrow 2, centered in the gap between the panels)
def arrow(xa, xb, y=580):
    d.rectangle([xa, y-20, xb-80, y+20], fill=AZUL)                 # shaft
    d.polygon([(xb, y), (xb-90, y-55), (xb-90, y+55)], fill=AZUL)   # head
arrow(860, 1030)

# ---- panel 2: method
x0,y0,x1,y1=1070,200,1740,960
d.rounded_rectangle([x0,y0,x1,y1],radius=18,outline=BORDA,width=4)
d.text((x0+30,y0+24),"PU learning",font=font(44,bold=True),fill=AZUL)
passos=["Spy Technique + Gaussian NB","→ 9,055 reliable negatives","   inferred, not assumed","Random Forest (GEE)","Tested against random","   pseudo-negatives on","   withheld sectors"]
yy=y0+100
for t in passos:
    d.text((x0+30,yy),t,font=font(36),fill=(30,30,30)); yy+=68
d.text((x0+30,y1-120),"Open data · Google Earth Engine\nGitHub + Zenodo (MIT / CC-BY)",font=font(34),fill=VERDE)

# ---- arrow 2
arrow(1780, 1950)

# ---- panel 3: result (cropped FSIVI map)
x0,y0,x1,y1=1990,200,2596,960
d.rounded_rectangle([x0,y0,x1,y1],radius=18,outline=BORDA,width=4)
d.text((x0+30,y0+24),"Graded susceptibility",font=font(44,bold=True),fill=AZUL)
# FSIVI thumbnail from the revised Fig. 18 (red-yellow-blue scale), rendered from its PDF
import subprocess, tempfile, os
from pathlib import Path
HERE=Path(__file__).resolve().parent
tmp=tempfile.mkdtemp()
subprocess.run(["pdftoppm","-r","300","-png","-singlefile",str(HERE/"output"/"Fig18.pdf"),os.path.join(tmp,"fig18")],check=True)
m=Image.open(os.path.join(tmp,"fig18.png")).convert("RGB")
mw,mh=m.size
# central crop, resized to fit the panel
c=m.crop((int(mw*0.14),int(mh*0.05),int(mw*0.86),int(mh*0.78)))   # map interior, without legend and scale bar
tw=x1-x0-60; th=int(c.size[1]*tw/c.size[0])
maxh=400
if th>maxh: th=maxh; tw=int(c.size[0]*th/c.size[1])
c=c.resize((tw,th))
img.paste(c,(x0+30+( (x1-x0-60-tw)//2 ),y0+100))
d.text((x0+30,y0+120+th+16),"Withheld sectors: PU labels\nset a near-optimal threshold\n(Lee–Liu 1.40; best 1.42)\nHigher area precision than\nHAND or clustering",font=font(32,bold=True),fill=(30,30,30))
OUT=HERE/"output"
img.save(OUT/"graphical_abstract.tiff",dpi=(300,300),compression="tiff_lzw")
print("saved", img.size)
