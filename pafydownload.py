import pafy

# var scroll = setInterval(function(){ window.scrollBy(0, 1000)}, 1000);
# window.clearInterval(scroll); console.clear(); urls = $$('a'); urls.forEach(function(v,i,a){if (v.id=="video-title"){console.log('\t'+v.title+'\t'+v.href+'\t')}}); 


def mycb(total, recvd, ratio, rate, eta):
    
    print(recvd,'\t\t', ratio,'\t\t', eta)

pafy.set_api_key("AIzaSyCUwPjj8sdItdIyPwTJrZdcncdgH_ekg3E")

links =[]
with open('D:\Projects\PythonProjects\.venv\music\links.txt','r') as box:
    links = box.readlines()
for a in links:
    links[links.index(a)] = a.rstrip('\n')
print(links)

for a in links:
    bleh = a
    if bleh == "2":
        break
    condition = True
    while condition:
        try:
            pafy.set_api_key("AIzaSyCUwPjj8sdItdIyPwTJrZdcncdgH_ekg3E")
            songphase1 = pafy.new(bleh)
            print(songphase1.title)
            songphase2 = songphase1.getbestaudio(preftype='m4a')
            songphase3 = songphase2.download(filepath="E:\\Shaarav\\wastebin\\")
            condition = False
        except:
            pass


