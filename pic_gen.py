import os
_path=os.getcwd()
if not os.path.exists(_path+'/pic_data'):
    os.mkdir(_path+'/pic_data')#训练图片数据存放库
import captcha
