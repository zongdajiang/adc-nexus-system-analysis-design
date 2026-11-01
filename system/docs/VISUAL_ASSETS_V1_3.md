# 1.3 图片资产与生成说明

本轮使用内置 imagegen 工具生成一张新图，未调用 API/CLI，未复用第三方诊所照片。

| 文件 | 用途 | 属性 |
|---|---|---|
| `src/main/resources/web/images/home-care-v1.png` | 第一场景，医患沟通 | 继承 1.2 原创图 |
| `src/main/resources/web/images/home-clinic-v1.png` | 第二场景，诊室与牙椅 | 继承 1.2 原创图 |
| `src/main/resources/web/images/home-reception-v1.png` | 第三场景及接待说明 | 新生成，1672 × 941 PNG，已检查人物、柜台、留白与非重复场景 |

原始生成输出保留在本机 Codex generated_images 目录，项目内已保存最终副本。页面明示为原创生成场景，不作为真实机构、患者或客户案例。前三张图不再重复。界面、图标、时间表与表格使用代码绘制，不把生成图片充当可操作界面。

生成提示词（内置工具，generate，非 edit）：

> Use case: photorealistic-natural. Asset type: original 16:9 wide website hero photo for ADC Nexus dental practice management, third distinct scene in a set. Primary request: candid editorial photograph of an everyday modern Chinese dental clinic reception, a professional East Asian female receptionist in neat pale-blue uniform seated behind a clean light-oak counter, helping an adult male patient in ordinary clothes confirm a paper appointment card. People and counter located in the RIGHT half of frame, left 45% mostly softly lit off-white wall and muted sage interior with usable negative space for website text. Natural window daylight, believable small clinical reception rather than luxury hotel, tactile wood, matte surfaces, realistic skin, understated neutral ivory and teal palette, eye-level 35mm perspective, refined documentary quality with natural depth. One monitor facing away so no legible UI or patient information. No text, no signage, no logos, no watermark. Avoid dental treatment scene, dental chair, glamour posing, blue glow, plastic CGI textures, duplicated people, malformed hands. The receptionist and patient are different people than any prior generated images.
