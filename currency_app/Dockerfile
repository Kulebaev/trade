FROM python:3.11

COPY requirements.txt /workdir/
COPY currency_app/ /workdir/currency_app/

WORKDIR /workdir

RUN pip install -U -e .
# uvicorn currency_app.main:app --reload

# Run the application
CMD ["uvicorn", "currency_app.main:app", "--host", "0.0.0.0", "--port", "80"]