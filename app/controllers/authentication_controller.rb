require 'jwt'

class AuthenticationController < ApplicationController
  def login
    email = params[:email]
    password = params[:password]

    user = User.find_by(email: email)

    if user&.authenticate(password)
      p user
      payload = { user_id: user.id, email: user.email,
       first_name: user.first_name, date_of_birth: user.date_of_birth, 
       second_name: user.second_name, phone: user.phone, user_role: user.user_role,
       exp: Time.now.to_i + 60 * 60 }
      p payload
      token = JWT.encode(payload, Rails.application.secret_key_base, 'HS256')

      render json: { token: token, message: "Login successful" }, status: :ok
    else
      render json: { error: "Invalid email or password" }, status: :unauthorized
    end
  end

  def register
    email = params[:email]
    password = params[:password]
    confirm_password = params[:confirmPassword]
    date_of_birth = params[:dateOfBirth]
    first_name = params[:firstName]
    user_role = params[:userRole]

    if password != confirm_password
      render json: { error: "Passwords do not match" }, status: :unprocessable_entity
      return
    end

    user = User.create(
      email: email,
      password: password,
      date_of_birth: date_of_birth,
      first_name: first_name,
      user_role: user_role
    )

    if user.persisted?
      render json: { message: "User created successfully", user: user }, status: :created
    else
      render json: { error: user.errors.full_messages }, status: :unprocessable_entity
    end
  end

  def change_user_data
    p User.all
    email = params[:email]
    firstName = params[:firstName]
    secondName = params[:lastName]
    phoneNumber = params[:phoneNumber]
    dateBirth = params[:birthDate]
    p email
    user = User.find_by(email: email)
    p user
    user.update(first_name: firstName, date_of_birth: dateBirth, 
       second_name: secondName, phone: phoneNumber)
    render status: 200, json: user.to_json
  end

  def ping
    render status: 200, json: 'Pong!'.to_json
  end 

  def grant
    userid = params[:userid]
    user = User.find_by(userid: userid)
    user.update(user_role: 'doctor')
    render status: 200, json: 'You became doctor. Congratulations!'
  end
end
