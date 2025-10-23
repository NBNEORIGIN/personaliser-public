from app.packer.rect_packer import pack_first_fit, Rect

def test_packer_determinism():
    rects = [
        Rect(id=str(i), w=w, h=h)
        for i, (w,h) in enumerate([(140,90),(140,90),(140,90),(140,90),(140,90),(140,90)])
    ]
    placed1, _ = pack_first_fit(rects, bed_w=480, bed_h=330, margin=5, gutter=5, keepouts=[(0,0,20,330)], seed=42)
    placed2, _ = pack_first_fit(rects, bed_w=480, bed_h=330, margin=5, gutter=5, keepouts=[(0,0,20,330)], seed=42)
    assert [(p.x,p.y) for p in placed1] == [(p.x,p.y) for p in placed2]
    # ensure count stable
    assert len(placed1) == len(placed2)
