class ChatController < ApplicationController
	def send_message
		render status: 200, json: '212121'.to_json
	end

	def chat_messages
		render status: 200, json: '2123323221'.to_json
	end
end
