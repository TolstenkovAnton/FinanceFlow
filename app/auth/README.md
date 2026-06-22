```shell
# Создать приватный RSA (RS256) ключ
openssl genrsa -out jwt-private.pem 2048
```

```shell
# Создать публичный ключ в пару к приватному для сертификата
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
```