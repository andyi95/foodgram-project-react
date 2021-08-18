# Foodgram React Project
[![Foodgram app workflow](https://github.com/andyi95/foodgram-project-react/actions/workflows/foodgram.yml/badge.svg)](https://github.com/andyi95/foodgram-project-react/actions/workflows/foodgram.yml)
## Описание

**Foodgram** веб-приложение для обмена рецептами с элементами социальной сети, позволяющее создавать рецепты, устанавливать собственные теги, ингридиенты и списки покупок. При создании использовался следующий стек технологий: Python3, Django Rest Framework, PostgreSQL, Gunicorn, Docker.

## Демо-страница проекта

С запущенным проектом можно ознакомиться по адресу http://foodgram.blackberrystudio.com/. Документация API http://foodgram.blackberrystudio.com/api/docs/

Прямой доступ к API http://foodgram.blackberrystudio.com/api/


## Сборка и запуск проекта

#### Установка Docker и Docker-compose

*Применимо для дистрибутов Ubuntu, для установки на других ОС см. соответствующий раздел [документации Docker](https://docs.docker.com/get-docker/)*

```shell
# Установка необходимых пакетов для добавления стороннего репозитория
sudo apt update
sudo apt install \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common -y
# Установка GPG ключа и самого резопитория Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
# Загрузка и установка пакетов Docker
sudo apt install docker-ce docker-compose -y
```
Выполните перезагрузку и проверьте корректную работу Docker командами `service docker status` и `docker ps -a`. 


#### Установка и запуск

Развёртывание может проводиться двумя способами:

**GitHub Actions**

Для использования CI/CD решения GitHub Actions скопируйте (fork) репозиторий в свой GitHub профиль, в разделе Actions Secrets настроек создайте переменные согласно списку ниже и включите Workflow на вкладке Actions.
 
**Локальное развёртывание**

Склонируйте репозиторий на рабочий сервер командой `git clone https://github.com/andyi95/yamdb_final.git`, в каталоге проекта скопируйте `.env.sample` в файл `.env` и заполните переменные, после чего запустите контейнеры: `docker-compose up -d`.

**Переменные окружения**

 - `SECRET_KEY` - 20-и значный секретный ключ Django, использующийся для хранения cookie-сессий, генерации crsf-токенов и другой приватной информации. 
 - `DB_HOST`, `DB_PORT`  - имя контейнера и порт контейнера PostgreSQL сервера. При необходимости, возможна работа с PostgreSQL хост-машины, для конфигурации см. соответствующий [раздел](https://docs.docker.com/compose/networking/), посвященный настройке сети контейнеров.
  - `DB_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - название базы данных, имя пользователя и пароль соответственно.
  - `HOST`, `USER`, `SSH_KEY`/`PASSWORD`, `PASSPHRASE` (optional) - адрес, имя пользователя и закрытый SSH-ключ (с парольной фразой при защите ключа) либо пароль, использующийся для подключения к удалённому серверу при развёртывании через GitHub Actions. Подробнее о параметрах развертывания по SSH можно узнать из репозитория [ssh-action](https://github.com/appleboy/ssh-action)
  - `DB_ENGINE` (необязательный параметр) - библиотека подключения к базе данных Django, значение по умолчанию `django.db.backends.postgresql`
  - `TELEGRAM_TOKEN`, `TELEGRAM_TO` (только c GH Actions)  - токен бота и id получателя для отправки Telegram-уведомлений. Инструкцию по созданию бота и получению необходимой информации можно из [докуменации Telegram](https://core.telegram.org/bots#6-botfather)
 
 #### Инициализация

После успешного прохождения автоматических тестов и развёртывания, можно провести первичную настройку.
```shell
docker-compose exec web bash
python manage.py migrate
python manage.py collectstatic --no-input
exit
```
Данный скрипт выполнит индексацию статических файлов и настройку полей и связей базы данных.