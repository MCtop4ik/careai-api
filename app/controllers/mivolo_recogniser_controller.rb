class MivoloRecogniserController < ApplicationController
	def execute_python_script
	    a = 5
	    b = 10
	    command = "python3 app/controllers/script.py #{a} #{b}"
	    result = `#{command}`
	    render json: { result: result }
  	end

  	def mivolo_recognise
	    # a = "https://realnoevremya.ru/uploads/articles/28/e9/81b40d1f274abba0.jpg"
	    # command = "python3 MiVOLO-main/render.py #{a}"
	    # result = `#{command}`
	    # render json: { result: result }
	    render json: {age: 22, gender: 'male'}, status: 200
  	end
end
