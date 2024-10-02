#!/bin/bash                                                                                                                                                                                                   
OS=$(uname)

if [ ! -f "./zpcli.py" ]; then
  echo "you need to switch to directory with zpcli.py application."
  ecit 1
fi

if [ "$(whereis python3 | grep bin)" == "" ]; then
  echo "no python3, need to install.."
  apt install python3
  apt install python3-venv
fi

if [ "$(whereis pip | grep bin)" == "" ]; then
  echo "no pip, need to install.."
  apt install pip 
fi


APP_DIR=$HOME/bin/zpcli-app/zpcli

# rm old instance of the application if there is any
rm -rf $HOME/bin/zpcli-app
mkdir -p  $APP_DIR
cp ./* ${APP_DIR}/

# copy default commands settins if there's no
if [ -f ${HOME}/zpcli.yaml ]; then
  mv ${HOME}/zpcli.yaml ${HOME}/.zpcli.yaml
elif [ ! -f ${HOME}/.zpcli.yaml ]; then
  cp ./zpcli.yaml ${HOME}/.zpcli.yaml
fi

pushd $APP_DIR

# create venv and install requirements
# mac os
# /opt/homebrew/opt/python@3.10/bin/python3.10 -m venv venv
python3 -m venv venv
source venv/bin/activate
pip3 install -r ./requirements.txt


# create executavle bash with venv activation
echo "#!/bin/bash" > ./zpcli
echo "ZPCLI_DIR=$APP_DIR" >> ./zpcli
echo "source \$ZPCLI_DIR/venv/bin/activate" >> ./zpcli
echo "python3 \$ZPCLI_DIR/main.py \"\$1\" \"\$2\" \"\$3\"" >> ./zpcli


# recreate symlink to ~/bin to be command in path
rm -rf $HOME/bin/zpcli
ln -s $APP_DIR/zpcli ~/bin/zpcli
chmod ugo+x ../zpcli
