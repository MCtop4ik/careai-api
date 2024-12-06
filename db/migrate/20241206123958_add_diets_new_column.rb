class AddDietsNewColumn < ActiveRecord::Migration[6.1]
  def change
    add_column :diets, :status, :string
  end
end
