import ffmpy
from ffmpy import FFmpeg
import os

a = os.listdir('E:\\Shaarav\\wastebin\\')
errors = []
for b in a:
    print(b)
    if '.m4a' in b:
        old_file = 'E:\\Shaarav\\wastebin\\' + b
        b = b.replace('.m4a','.mp3')
        new_file = 'E:\\Shaarav\\music\\' + b
        try:
            ff = FFmpeg(
                inputs = {old_file: None},
                outputs= {new_file:'-ac 2'}
            )
            ff.run()
        except Exception as e:
            errors.append([e,b])
        #os.remove(old_file)
print(errors)
