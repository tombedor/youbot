# shell script to change to MemGPT dir, pull upstream, checkout upstream/main, update a local branch called upstream to it.
# add commit bd4622d55b147f960d052c4be4272225d4e15cb3 to upstream
cd ~/Development/MemGPT
git fetch upstream
git checkout upstream/main
git pull upstream main
git branch -D upstream
git checkout -b upstream
git cherry-pick bd4622d55b147f960d052c4be4272225d4e15cb3
git push -f origin upstream