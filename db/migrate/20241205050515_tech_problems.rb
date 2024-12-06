class TechProblems < ActiveRecord::Migration[6.1]
  def change
    create_table :tech_problems do |t|
      t.string :userid
      t.string :subject
      t.string :question

      t.timestamps
    end
  end
end
