# MIN NUM OF ARG
if [[ "$#" < "1" ]]; then
    echo "Usage : usage PROJECT_NAME [ARGUMENT_LIST]" >&2
    return 1
fi
alias ptcreate='poetry new'
alias ptenvactivate2='source $(poetry env info --path)/bin/activate'
alias ptadd='poetry add'

PROJECT_NAME=$1
if [[ ! -d ${PROJECT_NAME} ]];then
    ptcreate ${PROJECT_NAME}
fi

if [[ -d ${PROJECT_NAME} ]];then
  cd ${PROJECT_NAME}
  ptenvactivate2
  if [[ ! -f .env ]];then
    echo "OPENAI_API_KEY=sk-xxx" > .env
  fi

  ptadd python-dotenv openai temporalio
  
  FILE=run_worker.py
  if [[ ! -f ${FILE} ]];then
    cp ../_templates_/${FILE} ./${FILE}
  fi
fi
