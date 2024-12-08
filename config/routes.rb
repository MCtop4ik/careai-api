Rails.application.routes.draw do
  # For details on the DSL available within this file, see https://guides.rubyonrails.org/routing.html
  post "/login", to: "authentication#login"
  get "/ping", to: "authentication#ping"
  post "/register", to: "authentication#register"
  post "/tech-problem", to: "tech_support#tech_message"
  post "/apply-diet", to: "diet_manager#apply_diet"

  post "/send-message", to: "chat#send_message"
  get "/messages", to: "chat#chat_messages"

  get "/all_diets", to: "diet_manager#all_diets"

  put "/change-user", to: "authentication#change_user_data"
  put "/approve-diet", to: "diet_manager#approve_diet"
  put "/disapprove-diet", to: "diet_manager#disapprove_diet"

  get "user-diets", to: "diet_manager#user_diets"
  post 'giga-chat/chat-completion', to: 'giga_chat#chat_completion'
  get 'execute_python_script', to: 'mivolo_recogniser#execute_python_script'
  get 'mivolo', to: 'mivolo_recogniser#mivolo_recognise'
  post 'grant', to: "authentication#grant"
end
