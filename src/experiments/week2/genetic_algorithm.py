"""Week 2 GA permutation baseline with EV/TW repair."""

from __future__ import annotations

import random
import time

from evrp_tw_common import EvalResult, Instance, check_solution, split_and_repair


def solve_genetic_algorithm(
    instance: Instance, population_size: int = 48, generations: int = 80
) -> EvalResult:
    begin = time.perf_counter()
    rng = random.Random(instance.seed + instance.scale + 17)
    customer_ids = [node.idx for node in instance.customers]

    def fitness(chromosome: list[int]) -> tuple[float, list[list[int]], bool, list[str]]:
        # A chromosome is only a customer permutation. The split-and-repair step
        # turns that sequence into routes before feasibility can be evaluated.
        routes = split_and_repair(instance, chromosome)
        feasible, cost, violations = check_solution(instance, routes)
        # Penalize constraint violations strongly so feasible solutions dominate
        # infeasible short routes during selection.
        penalty = 100000.0 * len(violations) + 10000.0 * max(0, len(routes) - instance.max_vehicles)
        return cost + penalty, routes, feasible, violations

    def crossover(a: list[int], b: list[int]) -> list[int]:
        # Order crossover keeps a contiguous section from parent A and fills the
        # rest using parent B without duplicating customers.
        left = rng.randrange(0, len(a))
        right = rng.randrange(left + 1, len(a) + 1)
        section = a[left:right]
        return section + [gene for gene in b if gene not in section]

    def mutate(chromosome: list[int]) -> None:
        # Swap explores local customer assignment changes; segment reversal is a
        # simple route-shape improvement similar to a weak 2-opt move.
        if rng.random() < 0.45:
            i, j = rng.sample(range(len(chromosome)), 2)
            chromosome[i], chromosome[j] = chromosome[j], chromosome[i]
        if rng.random() < 0.25:
            i, j = sorted(rng.sample(range(len(chromosome)), 2))
            chromosome[i:j] = reversed(chromosome[i:j])

    # Seed the population with one reasonable time-window order, then add random
    # permutations so the GA still explores a broad search space.
    base = sorted(customer_ids, key=lambda idx: instance.node(idx).ready)
    population = [base]
    for _ in range(population_size - 1):
        chromosome = customer_ids[:]
        rng.shuffle(chromosome)
        population.append(chromosome)

    best_score = float("inf")
    best_routes: list[list[int]] = []
    best_feasible = False
    best_violations: list[str] = []
    generation = 0
    stagnant = 0

    for generation in range(generations):
        ranked = sorted((fitness(chromosome)[0], chromosome) for chromosome in population)
        _, leader = ranked[0]
        leader_score, leader_routes, leader_feasible, leader_violations = fitness(leader)
        if leader_score + 1e-7 < best_score:
            best_score = leader_score
            best_routes = leader_routes
            best_feasible = leader_feasible
            best_violations = leader_violations
            stagnant = 0
        else:
            stagnant += 1

        # Elitism preserves the best current chromosomes while crossover and
        # mutation generate the next population.
        elites = [chromosome[:] for _, chromosome in ranked[: max(4, population_size // 6)]]
        next_population = elites[:]
        while len(next_population) < population_size:
            parent_a = rng.choice(elites)
            parent_b = rng.choice(population)
            child = crossover(parent_a, parent_b)
            mutate(child)
            next_population.append(child)
        population = next_population
        if best_feasible and stagnant >= 25 and generation >= 35:
            # Stop early after a feasible solution has stopped improving.
            break

    feasible, cost, violations = check_solution(instance, best_routes)
    return EvalResult(
        method="GA permutation + EV/TW repair",
        scale=instance.scale,
        objective=round(cost, 2) if feasible else None,
        feasible=feasible,
        runtime_sec=round(time.perf_counter() - begin, 3),
        vehicles_used=len(best_routes),
        routes=best_routes,
        convergence=(
            f"population={population_size}, generations_run={generation + 1}, "
            f"best_feasible={best_feasible}"
        ),
        violations=violations or best_violations,
    )
