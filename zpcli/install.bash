#!/bin/bash                                                                                                                                                                                                   

if [ ! -f "./zpcli.py" ]; then
  echo "you need to switch to directory with zpcli.py application."
  ecit 1
fi

if [ "$(whereis python3 | grep bin)" == "" ]; then
  echo "no python3, need to install.."
  apt install python3
fi

if [ "$(whereis pip | grep bin)" == "" ]; then
  echo "no pip, need to install.."
  apt install pip 
fi


APP_DIR=$HOME/bin/zpcli-app/zpcli

rm -rf $HOME/bin/zpcli-app
mkdir -p  $APP_DIR
cp ./* ${APP_DIR}/

if [ -f ${HOME}/zpcli.yaml ]; then
  mv ${HOME}/zpcli.yaml ${HOME}/.zpcli.yaml
elif [ ! -f ${HOME}/.zpcli.yaml ]; then
  cp ./zpcli.yaml ${HOME}/.zpcli.yaml
fi

pushd $APP_DIR
pip install pipenv
pipenv install
pipenv update

rm -rf $HOME/bin/zpcli
ln -s $APP_DIR/main.py ~/bin/zpcli
chmod ugo+x ../zpcli
