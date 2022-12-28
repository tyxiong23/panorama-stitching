import cv2
import numpy as np

class A(object):
    def __init__(self, a, b) -> None:
        self.h = None
        self.a = a
        self.b = b


    @property
    def H(self):
        if not self.h:
            self.h = [1,2,3]
        return self.h

    # def __eq__(self, __o: object) -> bool:
    #     return self.a == __o.a

img = cv2.imread("inputs/dongcao/01.jpg")
print(img.shape)

theta = np.pi / 180 * 45
M = [np.cos(theta), -np.sin(theta), 100, np.sin(theta), np.cos(theta), -200, 0,0, 1]
M = np.array(M).reshape(3,3)
print(M)
img_warp = cv2.warpPerspective(np.ones_like(img, dtype=np.uint8), M, img.shape[1::-1])

print(np.unique(img_warp))
print(img_warp.shape)
# cv2.imshow("Warp", img_warp)
# cv2.waitKey(0)

a = A(1,2)
b = A(1,3)
c = a; c.a = 2
print(a.H, a.a)
print(a == b, set([a,b]))

ss = [i for i in range(10)]

i = 0
while(i < len(ss)):
    print(i, ss)
    if (ss[i] % 2 == 0):
        ss.pop(i)
    else:
        i += 1