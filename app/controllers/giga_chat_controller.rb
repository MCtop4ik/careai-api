class GigaChatController < ApplicationController
  require 'net/http'
  require 'uri'
  require 'json'

  def chat_completion
  	meal_title = params[:meal_title]
    # URL для получения access_token
    token_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    token_payload = 'scope=GIGACHAT_API_PERS'
    token_headers = {
      'Content-Type' => 'application/x-www-form-urlencoded',
      'Accept' => 'application/json',
      'RqUID' => SecureRandom.uuid,
      'Authorization' => 'Basic ZmM4N2JiZDYtZjdhOS00ZGI3LWJjMjEtODYxYWE3ZDVlZDBjOmNlYzMwNjY5LTYzOTctNDNlOC04NTZjLTVkYjRmZDQzODU0OQ=='
    }

    # Получение access_token
    uri = URI.parse(token_url)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true
    http.verify_mode = OpenSSL::SSL::VERIFY_NONE # Отключение проверки SSL-сертификата
    request = Net::HTTP::Post.new(uri.request_uri, token_headers)
    request.body = token_payload
    token_response = http.request(request)
    token_data = JSON.parse(token_response.body)
    access_token = token_data['access_token']

    # URL для запроса к GigaChat
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    chat_headers = {
      'Authorization' => "Bearer #{access_token}"
    }
    chat_payload = {
      'model' => 'GigaChat',
      'messages' => [
        {
          'role' => 'system',
          'content' => 'Привет, ты повар в ресторане. Тебе официант принес название блюда. Придумай рецепт, и напиши его.\Пишешь сам рецепт текстом, пиши по действиям. Что куда бросить, размешать и тп. Сколько по времени готовить и в какой последовательности. Ты готовишь ' + meal_title
        }
      ],
      'profanity_check' => true
    }
    p chat_payload
    # Отправка запроса к GigaChat
    uri = URI.parse(chat_url)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true
    http.verify_mode = OpenSSL::SSL::VERIFY_NONE # Отключение проверки SSL-сертификата
    request = Net::HTTP::Post.new(uri.request_uri, chat_headers)
    request.body = chat_payload.to_json
    chat_response = http.request(request)

    if chat_response.is_a?(Net::HTTPSuccess)
      render json: JSON.parse(chat_response.body)
    else
      render json: { error: 'Failed to get response from GigaChat' }, status: :internal_server_error
    end
  end
end