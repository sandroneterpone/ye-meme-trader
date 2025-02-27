#!/bin/bash

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Iniziando pulizia Python...${NC}"

# 1. Termina processi Python
echo -e "\n${BLUE}📍 Terminando processi Python...${NC}"
pkill -9 -f python
pkill -9 -f python3

# 2. Pulisci cache pip
echo -e "\n${BLUE}📍 Pulendo cache pip...${NC}"
pip cache purge

# 3. Pulisci cache Python nella directory corrente (opzionale)
read -p "Vuoi pulire i file cache Python nella directory corrente? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "\n${BLUE}📍 Rimuovendo file cache Python...${NC}"
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -r {} +
fi

# 4. Pulisci file .DS_Store
read -p "Vuoi rimuovere i file .DS_Store? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "\n${BLUE}📍 Rimuovendo .DS_Store...${NC}"
    find . -type f -name ".DS_Store" -delete
fi

# 5. Verifica processi Python residui
echo -e "\n${BLUE}📍 Verificando processi Python residui...${NC}"
ps_output=$(ps aux | grep python | grep -v grep)
if [ -z "$ps_output" ]
then
    echo -e "${GREEN}✅ Nessun processo Python attivo${NC}"
else
    echo "Processi Python ancora attivi:"
    echo "$ps_output"
fi

# 6. Mostra memoria liberata
echo -e "\n${BLUE}📍 Statistiche memoria:${NC}"
df -h /System/Volumes/Data | tail -n 1 | awk '{print "Spazio disco disponibile: " $4}'

echo -e "\n${GREEN}✅ Pulizia completata!${NC}"
echo -e "${BLUE}Suggerimenti:${NC}"
echo "1. Usa 'pip list' per vedere i pacchetti installati"
echo "2. Usa 'pip freeze > requirements.txt' per salvare le dipendenze"
echo "3. Usa 'python3 -m venv venv' per creare un nuovo ambiente virtuale"
