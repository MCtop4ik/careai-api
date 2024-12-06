class CreateUsers < ActiveRecord::Migration[6.1]
  def change
    create_table :users do |t|
      t.string :email
      t.string :first_name
      t.date :date_of_birth
      t.string :password_digest

      t.timestamps
    end
  end
end
