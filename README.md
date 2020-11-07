# Microblog

Small blog application created following the [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) by [Miguel Grinberg](https://github.com/miguelgrinberg)

## Installation

- Clone the repository then `cd` into it.
- Create the `venv` folder with `virtualenv venv`
- Source the venv with `source venv/bin/activate`
- Install the needed modules with `pip3 install -r requirements.txt`
- Do `export FLASK_APP=microblog.py`
- Launch the server using `flask run`

## Database migration

To update the database:
- `flask db migrate`
- `flask db upgrade`