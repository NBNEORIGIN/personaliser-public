from app.packer.rect_packer import Rect, pack_paginated

def test_pagination_two_beds_deterministic():
    rects = [Rect(id=str(i), w=140.0, h=90.0) for i in range(20)]
    beds1 = pack_paginated(rects, bed_w=480.0, bed_h=330.0, margin=5.0, gutter=5.0, keepouts=[(0.0,0.0,20.0,330.0)], seed=42)
    beds2 = pack_paginated(rects, bed_w=480.0, bed_h=330.0, margin=5.0, gutter=5.0, keepouts=[(0.0,0.0,20.0,330.0)], seed=42)

    # Expect > 1 bed (12 per bed -> 2 beds for 20)
    assert len(beds1) >= 2

    # Deterministic: same number of beds and identical placements
    assert len(beds1) == len(beds2)
    for b1, b2 in zip(beds1, beds2):
        assert len(b1) == len(b2)
        for p1, p2 in zip(b1, b2):
            assert p1.id == p2.id
            assert p1.x == p2.x and p1.y == p2.y
            assert p1.w == p2.w and p1.h == p2.h
