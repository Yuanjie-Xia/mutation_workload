import urllib.request
import os


os.system('sudo docker stop teastore-all')
os.system('sudo docker rm teastore-all')
os.system('sudo docker run --cpus=2 -m=4GB -e "DB_HOST=sense02" -p 8080:8080 -d '
            '--name teastore-all descartesresearch/teastore-all')
os.system('sudo docker cp ~/mutation_workload/server.xml teastore-all:/usr/local/tomcat/conf')
os.system('sudo docker restart teastore-all')
code = urllib.request.urlopen("192.168.165.201:8080/tools.descartes.teastore.webui").getcode()
while code !=200:
    code = urllib.request.urlopen("192.168.165.201:8080/tools.descartes.teastore.webui").getcode()
    print(code)
    