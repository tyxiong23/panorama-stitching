# panorama-stitching 全景图像拼接

Course Project of Virtual Reality

成员：熊天翼，潘紫琪，弋紫轩

~~~
需涵盖的内容包括：实现方案、难点及解决方案、不足之处和可能的改进方案、【组员分工情况】等。
~~~

### 使用方式

~~~
python main.py <input-dir> --blending [no/simple/mbb]
~~~
输出位于`input-dir/result`

### 代码框架

~~~
工作路径
|-- inputs
|-- src # 源代码
|-- main.py # 主程序
~~~

#### Stitcher
封装了全景拼接所需的全部功能，包括载入input图片，SIFT，相关图片的matching，并计算每个输入图片的H矩阵，匹配全景图，并最后生成结果

#### Matcher
用于通过特征点找到匹配的图片对，并得到connected-components（每个component对应一张全景图，以及全景图中各图片的相关关系）

#### PairMatch
用于表示一对匹配上的图片（A and B），可用于判断匹配是否有效（valid）、计算Homograhy矩阵

### 小组分工
- 熊天翼：完成全景图像拼接的python代码基础框架（SIFT + 特征点匹配 + matching + 拼接），实现了多图拼接和simple blending功能。
