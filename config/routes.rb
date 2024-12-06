Rails.application.routes.draw do
  # For details on the DSL available within this file, see https://guides.rubyonrails.org/routing.html
  post "/login", to: "authentication#login"
  get "/ping", to: "authentication#ping"
  post "/register", to: "authentication#register"
  post "/tech-problem", to: "tech_support#tech_message"
  post "/apply-diet", to: "diet_manager#apply_diet"

  post "/send-message", to: "chat#send_message"
  get "/messages", to: "chat#chat_messages"

  get "all_diets", to: "diet_manager#all_diets"
end
