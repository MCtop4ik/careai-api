class DietManagerController < ApplicationController
	def apply_diet
		userid = params[:userid]
		diet = params[:diet]
		status = params[:status]

		diets = Diets.create(userid: userid, diet: diet, status: status)
		render status: 200, json: diets.to_json
	end

	def all_diets
		diets = Diets.all
		render status: 200, json: diets.to_json
	end
end
