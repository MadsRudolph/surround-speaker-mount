# Units: millimetres. X right, Y away from wall, Z up.
DEFAULTS = dict(Speaker_Width=150., Speaker_Depth=150., Speaker_Height=180.,
    Clamp_Padding_Offset=2., Insert_Hole_Diameter=5.6, Wall_Thickness=4.)
NAMES = ['Part_1_WallPlate', 'Part_2_SwivelArm', 'Part_3_Cradle']
YAW = (0.,55.,24.)
PITCH = (0.,110.,24.)

def geometry(p):
    w,d,h,pad,insert,t = [p[k] for k in DEFAULTS]
    if not (100 <= w <= 200 and 100 <= d <= 200 and 120 <= h <= 240
            and 1 <= pad <= 3 and 4 <= t <= 6 and 5 <= insert <= 6.5):
        raise ValueError('Parameters outside supported geometry envelope; redesign required.')
    parts=[([],[]) for _ in range(3)]
    def box(i,lo,hi,r=1.,cut=False):
        parts[i][int(cut)].append(('box',lo,hi,r))
    def cyl(i,pos,r,length,axis='Z',edge=.4,cut=False):
        parts[i][int(cut)].append(('cyl',pos,r,length,axis,edge))
    # Wall plate; horizontal ears provide the vertical yaw axis.
    box(0,(-45,0,-31),(45,2*t,109),2)
    for z in (0,36):
        box(0,(-22,4,z),(22,55,z+12),1)
        cyl(0,(0,55,z),22,12)
    # Broad root reinforcement, clear of the moving middle knuckle.
    box(0,(-26,4,-14),(26,22,12),2)
    box(0,(-26,4,36),(26,22,62),2)
    cyl(0,(0,55,-2),2.65,52,cut=True,edge=0)
    for x in (-30,30):
        for z in (-16,94):
            cyl(0,(x,-1,z),2.4,2*t+2,'Y',0,True)
            cyl(0,(x,2*t-3,z),5,4,'Y',0,True)
    # 45-degree lead-in chamfers to the counterbores.
    for x in (-30,30):
        for z in (-16,94):
            parts[0][1].append(('cone',(x,2*t-.6,z),4.9,5.6,.7,'Y'))
    # Intermediate arm: 0.3 mm clearance at each friction face.
    cyl(1,(0,55,12.3),22,23.4)
    box(1,(-16,55,16),(16,78,32),2)
    box(1,(-24.3,65,12),(24.3,81,36),2)
    for x in (-24.3,12.3):
        box(1,(x,75,2),(x+12,110,46),1)
        cyl(1,(x,110,24),22,12,'X')
    cyl(1,(0,55,11),2.65,26,cut=True,edge=0)
    cyl(1,(-26,110,24),2.65,52,'X',0,True)
    # Low pitch joint and short rear bridge stay below the terminal panel.
    # Panel lower edge: shelf 10 + foam 2 + cabinet offset 40 = Z52.
    cyl(2,(-12,110,24),22,24,'X')
    box(2,(-12,110,12),(12,143,36),2)
    box(2,(-38,135,12),(38,147,36),2)
    for x in (-38,24):
        box(2,(x,135,6),(x+14,147,34),2)
    inner=w/2+pad+4 # 4 mm reserved for commercial swivel pressure feet.
    side=2*t
    front=145+d+2*pad
    shelf=max(10,2*t)
    box(2,(-inner-side,135,0),(inner+side,front+t,shelf),2)
    box(2,(-inner-side,front,6),(inner+side,front+t,26),1)
    for sign in (-1,1):
        lo,hi=((-inner-side,-inner) if sign<0 else (inner,inner+side))
        box(2,(lo,145,6),(hi,front+t,h*.38),1)
        for y in (145+d*.30,145+d*.75):
            # Boss extends outward; 12 mm depth for a 6 mm long insert.
            x=(-inner-side-4 if sign<0 else inner)
            cyl(2,(x,y,h*.27),10,side+4,'X')
            cyl(2,(x-1,y,h*.27),insert/2,side+6,'X',0,True)
    cyl(2,(-14,110,24),2.65,28,'X',0,True)
    return parts
