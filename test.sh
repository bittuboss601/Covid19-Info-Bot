PORT=$(< endpoints.yml sed -n -e 's/.localhost:\([0-9]\{4\}\).*/\1/p' | sed -n -e 's/.*\([0-9]\{4\}\).*/\1/p')
echo $PORT
