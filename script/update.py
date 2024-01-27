git stash && git pull origin main
poetry update pymemgpt
git add poetry.config
git commit -m 'update poetry config'
