# newsletter — Encontrarás Tudo

- `template.html` — template visual (wrapper) da newsletter, no formato do Listmonk
  (contém `{{ template "content" . }}`, `{{ UnsubscribeURL }}`, `{{ TrackView }}`).
  Registrado no Listmonk via API. A copy de cada envio entra no "content".
