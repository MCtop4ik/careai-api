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

	def approve_diet
		id = params[:id]
		status = 'approved'
		diet = params[:diet]

		p id, diet, params

		diet = Diets.find_by(id: id)
		diet.update(status: status)
		render status: 200, json: diet.to_json
	end

	def disapprove_diet
		id = params[:id]
		status = 'disapproved'
		diet = params[:diet]

		p id, diet, params

		diet = Diets.find_by(id: id)
		diet.update(status: status)
		render status: 200, json: diet.to_json
	end

	def user_diets
		userid = params[:userid]
		diets = Diets.where(userid: userid)
		p diets
		render status: 200, json: diets.to_json
	end
end
