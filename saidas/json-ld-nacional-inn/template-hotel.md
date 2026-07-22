# Template de dados estruturados · Rede Nacional Inn

> Arquivo **técnico, interno**. É a ficha que a IA lê. Não vai pra peça de cliente.
> Mesmo padrão do `@graph` que o site mariolucash.com.br usa pra passar na própria auditoria.
>
> Como usar: copiar o bloco `<script type="application/ld+json">` pro `<head>` da
> página de cada hotel, trocar cada `{{PLACEHOLDER}}` pelo dado real daquele hotel,
> e validar em https://validator.schema.org e no Rich Results Test do Google.
>
> Cobre as informações essenciais que a IA procura e hoje não encontra: identidade
> do hotel, endereço, geo, telefone, faixa de preço, classificação, nota, comodidades,
> check-in/out e o link de **reserva direta** (pra tirar a resposta das mãos das OTAs).

---

## 1. Template genérico (um por hotel)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Hotel",
      "@id": "{{URL_HOTEL}}#hotel",
      "name": "{{NOME_DO_HOTEL}}",
      "url": "{{URL_HOTEL}}",
      "image": "{{URL_FOTO_PRINCIPAL}}",
      "description": "{{DESCRICAO_1_2_FRASES_COM_DESTINO}}",
      "priceRange": "{{FAIXA_EX_R$_250_R$_600}}",
      "currenciesAccepted": "BRL",
      "telephone": "{{TELEFONE_+55...}}",
      "email": "{{EMAIL_RESERVAS}}",
      "starRating": { "@type": "Rating", "ratingValue": "{{ESTRELAS_EX_3}}" },
      "petsAllowed": {{true_ou_false}},
      "checkinTime": "{{HH:MM_EX_14:00}}",
      "checkoutTime": "{{HH:MM_EX_12:00}}",
      "numberOfRooms": "{{QTD_QUARTOS}}",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "{{RUA_NUMERO}}",
        "addressLocality": "{{CIDADE}}",
        "addressRegion": "{{UF_EX_SP}}",
        "postalCode": "{{CEP}}",
        "addressCountry": "BR"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": "{{LAT}}",
        "longitude": "{{LNG}}"
      },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "{{NOTA_EX_8.9_ou_4.5}}",
        "reviewCount": "{{QTD_AVALIACOES}}",
        "bestRating": "{{ESCALA_EX_10_ou_5}}"
      },
      "amenityFeature": [
        { "@type": "LocationFeatureSpecification", "name": "Wi-Fi gratuito", "value": true },
        { "@type": "LocationFeatureSpecification", "name": "Café da manhã incluso", "value": true },
        { "@type": "LocationFeatureSpecification", "name": "Estacionamento", "value": true },
        { "@type": "LocationFeatureSpecification", "name": "Piscina", "value": {{true_ou_false}} },
        { "@type": "LocationFeatureSpecification", "name": "Aceita pets", "value": {{true_ou_false}} }
      ],
      "makesOffer": {
        "@type": "Offer",
        "name": "Reserva direta no site oficial",
        "url": "{{URL_RESERVA_DIRETA}}",
        "priceCurrency": "BRL"
      },
      "potentialAction": {
        "@type": "ReserveAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "{{URL_RESERVA_DIRETA}}",
          "inLanguage": "pt-BR",
          "actionPlatform": [
            "http://schema.org/DesktopWebPlatform",
            "http://schema.org/MobileWebPlatform"
          ]
        },
        "result": { "@type": "LodgingReservation", "name": "Reserva de hospedagem" }
      },
      "brand": { "@id": "https://www.nacionalinn.com.br/#rede" },
      "parentOrganization": { "@id": "https://www.nacionalinn.com.br/#rede" }
    },
    {
      "@type": "HotelChain",
      "@id": "https://www.nacionalinn.com.br/#rede",
      "name": "Rede Nacional Inn Hotéis",
      "url": "https://www.nacionalinn.com.br/",
      "logo": "https://www.nacionalinn.com.br/{{CAMINHO_LOGO}}",
      "sameAs": [
        "https://www.instagram.com/redenacionalinn/",
        "https://www.facebook.com/RedeNacionalInn/"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "{{URL_HOTEL}}#website",
      "url": "{{URL_HOTEL}}",
      "name": "{{NOME_DO_HOTEL}}",
      "inLanguage": "pt-BR",
      "publisher": { "@id": "https://www.nacionalinn.com.br/#rede" }
    }
  ]
}
</script>
```

---

## 2. Exemplo preenchido (piloto Campos do Jordão)

> Valores abaixo são **placeholders realistas** para ilustrar o formato final.
> Confirmar cada dado (nota, nº de avaliações, coordenadas, CEP, telefone, URL de
> reserva) com o time da rede antes de publicar. Não inventar número, ver preferências.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Hotel",
      "@id": "https://www.nacionalinn.com.br/campos-do-jordao#hotel",
      "name": "Nacional Inn Campos do Jordão",
      "url": "https://www.nacionalinn.com.br/campos-do-jordao",
      "image": "https://www.nacionalinn.com.br/img/campos-do-jordao/fachada.jpg",
      "description": "Hotel da Rede Nacional Inn em Campos do Jordão, na Serra da Mantiqueira, com café da manhã incluso e reserva direta pelo site oficial.",
      "priceRange": "R$ 300 – R$ 700",
      "currenciesAccepted": "BRL",
      "telephone": "+55-12-XXXX-XXXX",
      "email": "reservas.campos@nacionalinn.com",
      "starRating": { "@type": "Rating", "ratingValue": "3" },
      "petsAllowed": false,
      "checkinTime": "14:00",
      "checkoutTime": "12:00",
      "numberOfRooms": "XX",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "{{RUA_NUMERO}}",
        "addressLocality": "Campos do Jordão",
        "addressRegion": "SP",
        "postalCode": "{{CEP}}",
        "addressCountry": "BR"
      },
      "geo": { "@type": "GeoCoordinates", "latitude": "{{LAT}}", "longitude": "{{LNG}}" },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "{{NOTA}}",
        "reviewCount": "{{QTD}}",
        "bestRating": "10"
      },
      "amenityFeature": [
        { "@type": "LocationFeatureSpecification", "name": "Wi-Fi gratuito", "value": true },
        { "@type": "LocationFeatureSpecification", "name": "Café da manhã incluso", "value": true },
        { "@type": "LocationFeatureSpecification", "name": "Estacionamento", "value": true }
      ],
      "makesOffer": {
        "@type": "Offer",
        "name": "Reserva direta no site oficial",
        "url": "https://www.nacionalinn.com.br/campos-do-jordao/reservas",
        "priceCurrency": "BRL"
      },
      "potentialAction": {
        "@type": "ReserveAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "https://www.nacionalinn.com.br/campos-do-jordao/reservas",
          "inLanguage": "pt-BR",
          "actionPlatform": [
            "http://schema.org/DesktopWebPlatform",
            "http://schema.org/MobileWebPlatform"
          ]
        },
        "result": { "@type": "LodgingReservation", "name": "Reserva de hospedagem" }
      },
      "brand": { "@id": "https://www.nacionalinn.com.br/#rede" },
      "parentOrganization": { "@id": "https://www.nacionalinn.com.br/#rede" }
    },
    {
      "@type": "HotelChain",
      "@id": "https://www.nacionalinn.com.br/#rede",
      "name": "Rede Nacional Inn Hotéis",
      "url": "https://www.nacionalinn.com.br/",
      "logo": "https://www.nacionalinn.com.br/img/logo.png",
      "sameAs": [
        "https://www.instagram.com/redenacionalinn/",
        "https://www.facebook.com/RedeNacionalInn/"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.nacionalinn.com.br/campos-do-jordao#website",
      "url": "https://www.nacionalinn.com.br/campos-do-jordao",
      "name": "Nacional Inn Campos do Jordão",
      "inLanguage": "pt-BR",
      "publisher": { "@id": "https://www.nacionalinn.com.br/#rede" }
    }
  ]
}
</script>
```

---

## 3. Checklist de publicação (por hotel)

- [ ] Um bloco por página de hotel, com `@id` único apontando pra URL daquela página.
- [ ] `HotelChain` da rede sempre com o mesmo `@id`, pra IA entender que os hotéis são a mesma rede.
- [ ] Dados verificados com o time (nota, avaliações, telefone, CEP, coordenadas, URL de reserva).
- [ ] `makesOffer` e `potentialAction` apontando pra **reserva direta**, nunca pra OTA.
- [ ] Validar em validator.schema.org + Rich Results Test antes de subir.
- [ ] Sem alterar visual, pixels de conversão ou fluxo de reserva. Só o `<head>`.
