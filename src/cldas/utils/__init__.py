from cldas.utils.logger import Log, Level
from cldas.utils.file import save, load, save_word_cloud
from cldas.utils.visual import progress, title, RGBGradiant
from cldas.utils import metrics
from cldas.utils.graph import MultiGraph

USEFUL_TAGS = [
    'AQ', # Adjetivo calificativos     - p.e. alegre   
    'RG', # Adverbio General           - p.e. despacio 
    'DD', # Determinante Demostrativo  - p.e. este     
    'NC', # Nombre Comun               - p.e. gato     
    'VM', # Verbo Principal            - p.e. Pedro    
    'PD', # Pronombre Demostrativo     - p.e. aquel    
    'PI'  # Pronombre Indefinido       - p.e. bastante 
]