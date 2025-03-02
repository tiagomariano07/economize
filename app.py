import re
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Configuração do Selenium WebDriver
options = Options()
options.add_argument("--headless")  # Executa sem abrir o navegador
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = input("Digite a URL da nota fiscal: ")

#url_assaí=https://www.fazenda.pr.gov.br/nfce/qrcode?p=41241106057223036796650180002368611184656991|2|1|1|A09D43DF4CF5B95D05AC2397D0976B5C46CE8F11

#url_muffato=https://www.fazenda.pr.gov.br/nfce/qrcode?p=41250276430438007001650200003228571020542839|2|1|1|0C2C3F0A13A1B8BF4EAAD535D8743A714BE3EA44

try:
    # Acessa a página
    driver.get(url)

    # Aguarda o carregamento da tabela de produtos
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )

    # Obtém o código HTML da página
    html = driver.page_source

finally:
    # Fecha o navegador
    driver.quit()

# Processa o HTML com BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Obtém os dados principais da nota fiscal
try:
    nome_estabelecimento = soup.find('div', id='u20').get_text(strip=True)
except AttributeError:
    nome_estabelecimento = "Não encontrado"

# Nome da aba com o nome do estabelecimento (removendo caracteres inválidos)
sheet_name = re.sub(r'[\/:*?"<>|]', '', nome_estabelecimento)[:31]  # Excel aceita até 31 caracteres

# Buscar todas as linhas de produtos na tabela
linhas = soup.find_all('tr', id=True)

# Lista para armazenar os dados extraídos
dados_extraidos = []

# Itera sobre as linhas da tabela e extrai os dados das colunas
for linha in linhas:
    # Garantir que o nome do estabelecimento seja atribuído a cada linha (caso não seja encontrado, usa o nome geral)
    nome_estabelecimento_item = soup.find('div', id='u20').get_text(strip=True) if linha.find('div', id='u20') else nome_estabelecimento
    
    txtTit2 = linha.find('span', class_='txtTit2').get_text(strip=True) if linha.find('span', class_='txtTit2') else ''
    Rcod = linha.find('span', class_='RCod').get_text(strip=True).replace("Código: ", "")
    Rcod = re.sub(r'[()]', '', Rcod)  # Remove os parênteses
    RUN = linha.find('span', class_='RUN').get_text(strip=True).replace("UN: ", "") if linha.find('span', class_='RUN') else ''
    Rvlunit = linha.find('span', class_='RvlUnit').get_text(strip=True).replace("Vl. Unit.:", "") if linha.find('span', class_='RvlUnit') else ''
    
    cnpj = soup.find('div', class_='text').get_text(strip=True).replace("CNPJ:", "").strip()
    cnpj = re.sub(r'\D', '', cnpj)  # Remove tudo que não for número
    divs = soup.find_all('div', class_='text')
    endereco = divs[1].get_text(strip=True)
    data_emissao = soup.find('strong', string=lambda text: 'Emissão:' in text).next_sibling.strip()
    data_emissao = re.match(r'\d{2}/\d{2}/\d{4}', data_emissao).group()
    
    # Adiciona os dados extraídos na lista
    dados_extraidos.append([txtTit2, Rcod, RUN, Rvlunit, nome_estabelecimento_item, cnpj, endereco, data_emissao])

# Cria um DataFrame com os dados extraídos
df_novo = pd.DataFrame(dados_extraidos, columns=['Produto', 'Código', 'Unidade', 'Valor Unitário', 'Nome Estabelecimento','CNPJ', 'Endereço', 'Data Emissão'])

# Nome do arquivo Excel
arquivo_excel = "conteudo_estruturado_site.xlsx"

# Verificar se o arquivo já existe
if os.path.exists(arquivo_excel):
    # Abrir o arquivo para adicionar a nova aba, substituindo a aba existente se necessário
    with pd.ExcelWriter(arquivo_excel, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
        # Cria a nova aba ou sobrescreve se já existir
        df_novo.to_excel(writer, sheet_name=sheet_name, index=False)

else:
    # Criar um novo arquivo com a aba correspondente
    with pd.ExcelWriter(arquivo_excel, mode="w", engine="openpyxl") as writer:
        df_novo.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Dados salvos na aba '{sheet_name}' do arquivo '{arquivo_excel}' com sucesso!")