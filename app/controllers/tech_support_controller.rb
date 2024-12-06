class TechSupportController < ApplicationController
	def tech_message
		subject = params[:subject]
		question = params[:question]
		tech_problems = TechProblems.create(
	      userid: '2121221',
	      subject: subject,
	      question: question
	    )
	    p subject, question
		render status: 200, json: tech_problems.to_json
	end
end
