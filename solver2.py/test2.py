dists = [45.880278987817846,
5.0990195135927845,
5.830951894845301,
5.0,
1.4142135623730951,
8.06225774829855,
2.23606797749979,
2.0,
5.0,
3.0,
3.1622776601683795,
3.0,
7.211102550927978]

demands = [0,0.5,1.62,1.16,0.5,1.34,0.76,0.5,0.5,0.5,0.5,0.5,0.77]

if len(dists) != len(demands):
    raise ValueError("The lengths of dists and demands must match.")

# Calculate the cumulative distances
cumulative_dists = []
cumulative_sum = 0
for dist in dists:
    cumulative_sum += dist
    cumulative_dists.append(cumulative_sum)

# Calculate cumulative demands (tons)
cumulative_demands = []
cumulative_load = 0
for demand in demands:
    cumulative_load += demand
    cumulative_demands.append(cumulative_load)

# Compute tons × kms
tons_kms = sum(cum_dist * cum_load for cum_dist, cum_load in zip(cumulative_dists, demands)) + sum(dists)*8

print(f"Total Cost: {tons_kms}")


node_to_move = demands.pop(1)  # Remove demand of node 1
demands.insert(3, node_to_move)  # Insert at the new position

dist_to_move = dists.pop(1)  # Remove distance of node 1
dists.insert(3, dist_to_move)

cumulative_dists = []
cumulative_sum = 0
for dist in dists:
    cumulative_sum += dist
    cumulative_dists.append(cumulative_sum)

# Calculate cumulative demands (tons)
cumulative_demands = []
cumulative_load = 0
for demand in demands:
    cumulative_load += demand
    cumulative_demands.append(cumulative_load)

# Compute tons × kms
tons_kms2 = sum(cum_dist * cum_load for cum_dist, cum_load in zip(cumulative_dists, demands)) + sum(dists)*8

print(f"Total Cost: {tons_kms2 -tons_kms}")