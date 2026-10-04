import AgtXIvRootMath.F2Coordinates
import AgtXIvRootMath.HermitianPauliBasis

/-! Uncompiled explicit JW family. Some(k,false/true) are the X/Y strings
with a Z prefix; none is global parity. The phase-clean representative may
differ by a sign from a chosen conventional Y string, so exact phase alignment
is not asserted. A legal nonidentity window requires n>0.
-/

namespace AgtXIv.JordanWigner

open AgtXIv.Stabilizer

noncomputable section

abbrev Index (n : ℕ) := Option (Fin n × Bool)

theorem index_card (n : ℕ) : Fintype.card (Index n) = 2 * n + 1 := by
  simp [Index, Nat.mul_comm]

def coordinates {n : ℕ} : Index n → ((Fin n → F2) × (Fin n → F2))
  | none => (fun _ => 1, fun _ => 0)
  | some (k, y) =>
      (fun j => if j < k ∨ (j = k ∧ y = true) then 1 else 0,
       fun j => if j = k then 1 else 0)

def support {n : ℕ} (i : Index n) : F2Support n :=
  (F2Support.coordinateEquiv n).symm (coordinates i)

theorem support_coordinates {n : ℕ} (i : Index n) :
    F2Support.coordinateEquiv n (support i) = coordinates i :=
  (F2Support.coordinateEquiv n).apply_symm_apply _

def observable {n : ℕ} (i : Index n) : Pauli n :=
  hermitianSupportPauli ((support i).1.bits, (support i).2.bits)

theorem observable_sq {n : ℕ} (i : Index n) : observable i ^ 2 = 1 :=
  hermitianSupportPauli_sq _

theorem observable_support {n : ℕ} (i : Index n) :
    F2Support.pauli (observable i) = support i := by
  ext <;> simp [F2Support.pauli, observable]

theorem coordinates_ne_zero {n : ℕ} (hn : 0 < n) (i : Index n) :
    coordinates i ≠ 0 := by
  intro h
  cases i with
  | none =>
    have hAt := congrArg (fun v : (Fin n → F2) × (Fin n → F2) => v.1 ⟨0, hn⟩) h
    have hFalse : (1 : F2) = 0 := by simpa [coordinates] using hAt
    exact one_ne_zero hFalse
  | some a =>
    obtain ⟨k, y⟩ := a
    have hAt := congrArg (fun v : (Fin n → F2) × (Fin n → F2) => v.2 k) h
    have hFalse : (1 : F2) = 0 := by simpa [coordinates] using hAt
    exact one_ne_zero hFalse

theorem support_ne_zero {n : ℕ} (hn : 0 < n) (i : Index n) : support i ≠ 0 := by
  intro h
  apply coordinates_ne_zero hn i
  rw [← support_coordinates i, h, map_zero]

theorem observable_nonidentitySupport {n : ℕ} (hn : 0 < n) (i : Index n) :
    F2Support.pauli (observable i) ≠ 0 := by
  rw [observable_support]
  exact support_ne_zero hn i

theorem coordinates_injective (n : ℕ) : Function.Injective (@coordinates n) := by
  intro a b h
  cases a with
  | none =>
    cases b with
    | none => rfl
    | some b =>
      obtain ⟨k, y⟩ := b
      have hAt := congrArg (fun v : (Fin n → F2) × (Fin n → F2) => v.2 k) h
      simp [coordinates] at hAt
  | some a =>
    obtain ⟨k, y⟩ := a
    cases b with
    | none =>
      have hAt := congrArg (fun v : (Fin n → F2) × (Fin n → F2) => v.2 k) h
      simp [coordinates] at hAt
    | some b =>
      obtain ⟨l, z⟩ := b
      have hPosition : k = l := by
        by_contra hne
        have hAt := congrArg (fun v : (Fin n → F2) × (Fin n → F2) => v.2 k) h
        simp [coordinates, hne] at hAt
      subst l
      have hAt := congrArg (fun v : (Fin n → F2) × (Fin n → F2) => v.1 k) h
      have hBool : y = z := by
        cases y <;> cases z <;> simp [coordinates] at hAt ⊢
      subst z
      rfl

theorem support_injective (n : ℕ) : Function.Injective (@support n) := by
  intro a b h
  apply coordinates_injective n
  simpa only [support_coordinates] using congrArg (F2Support.coordinateEquiv n) h

theorem observable_distinctPhaseClass (n : ℕ) :
    Function.Injective (fun i : Index n => F2Support.pauli (observable i)) := by
  simpa only [observable_support] using support_injective n

end
end AgtXIv.JordanWigner
