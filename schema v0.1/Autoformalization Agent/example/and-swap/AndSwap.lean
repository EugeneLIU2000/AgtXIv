namespace AutoformalizationExample

theorem and_swap (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  have hq : Q := h.right
  have hp : P := h.left
  have hqp : Q ∧ P := And.intro hq hp
  exact hqp

end AutoformalizationExample

#print AutoformalizationExample.and_swap
#print axioms AutoformalizationExample.and_swap
