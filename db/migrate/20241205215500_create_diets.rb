class CreateDiets < ActiveRecord::Migration[6.1]
  def change
    create_table :diets do |t|
      t.string :userid
      t.string :diet

      t.timestamps
    end
  end
end
