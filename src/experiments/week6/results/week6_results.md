# Week 6 Results: Integrated Portfolio and Adaptive Operator Selection

Run started: `2026-08-13 17:29:49 CST`

Does a nearest/composite portfolio improve on Method D, and can UCB1 adaptive operator selection improve the quality/runtime trade-off?

## Aggregate results

| Profile | n | Method | Feasible | Rate | Mean objective | Median | Best | Runtime (s) | Initial improvement (%) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | B_nearest_customer | 12/12 | 1.000 | 477.272 | 469.198 | 419.505 | 0.000266 | 0.00 |
| baseline | 20 | D_composite_inter_route | 12/12 | 1.000 | 421.546 | 427.623 | 334.520 | 0.006252 | 0.00 |
| baseline | 20 | E_fixed_portfolio | 12/12 | 1.000 | 406.754 | 409.427 | 334.520 | 0.012044 | 14.46 |
| baseline | 20 | E_adaptive_portfolio | 12/12 | 1.000 | 405.322 | 409.427 | 334.520 | 0.015490 | 14.96 |
| baseline | 50 | B_nearest_customer | 12/12 | 1.000 | 704.552 | 705.492 | 574.819 | 0.001645 | 0.00 |
| baseline | 50 | D_composite_inter_route | 12/12 | 1.000 | 675.434 | 658.774 | 581.979 | 0.116132 | 0.00 |
| baseline | 50 | E_fixed_portfolio | 12/12 | 1.000 | 623.753 | 631.163 | 555.296 | 0.212197 | 14.61 |
| baseline | 50 | E_adaptive_portfolio | 12/12 | 1.000 | 626.176 | 631.468 | 555.296 | 0.190270 | 13.26 |
| baseline | 100 | B_nearest_customer | 12/12 | 1.000 | 1128.933 | 1124.210 | 1001.897 | 0.007395 | 0.00 |
| baseline | 100 | D_composite_inter_route | 12/12 | 1.000 | 1006.763 | 995.729 | 917.062 | 0.924082 | 0.00 |
| baseline | 100 | E_fixed_portfolio | 12/12 | 1.000 | 943.556 | 950.564 | 862.376 | 1.803978 | 17.65 |
| baseline | 100 | E_adaptive_portfolio | 12/12 | 1.000 | 946.283 | 948.930 | 842.444 | 1.212568 | 16.46 |
| tight_tw | 20 | B_nearest_customer | 12/12 | 1.000 | 480.401 | 477.123 | 419.505 | 0.000273 | 0.00 |
| tight_tw | 20 | D_composite_inter_route | 12/12 | 1.000 | 421.010 | 433.619 | 334.520 | 0.006655 | 0.00 |
| tight_tw | 20 | E_fixed_portfolio | 12/12 | 1.000 | 408.729 | 407.148 | 334.520 | 0.012072 | 13.41 |
| tight_tw | 20 | E_adaptive_portfolio | 12/12 | 1.000 | 407.125 | 407.148 | 334.520 | 0.015598 | 13.76 |
| tight_tw | 50 | B_nearest_customer | 12/12 | 1.000 | 711.661 | 709.292 | 574.819 | 0.001435 | 0.00 |
| tight_tw | 50 | D_composite_inter_route | 12/12 | 1.000 | 651.803 | 653.920 | 578.851 | 0.117561 | 0.00 |
| tight_tw | 50 | E_fixed_portfolio | 12/12 | 1.000 | 624.591 | 630.177 | 555.296 | 0.201290 | 15.09 |
| tight_tw | 50 | E_adaptive_portfolio | 12/12 | 1.000 | 622.545 | 631.106 | 555.296 | 0.187896 | 15.37 |
| tight_tw | 100 | B_nearest_customer | 12/12 | 1.000 | 1135.976 | 1134.883 | 1014.350 | 0.007325 | 0.00 |
| tight_tw | 100 | D_composite_inter_route | 12/12 | 1.000 | 1012.140 | 1013.603 | 944.990 | 0.948134 | 0.00 |
| tight_tw | 100 | E_fixed_portfolio | 12/12 | 1.000 | 950.402 | 954.725 | 880.659 | 1.872617 | 16.10 |
| tight_tw | 100 | E_adaptive_portfolio | 12/12 | 1.000 | 958.843 | 960.012 | 868.831 | 1.191284 | 15.42 |
| small_battery | 20 | B_nearest_customer | 10/12 | 0.833 | 491.950 | 488.923 | 443.391 | 0.000271 | 0.00 |
| small_battery | 20 | D_composite_inter_route | 11/12 | 0.917 | 468.292 | 464.134 | 407.102 | 0.006802 | 0.00 |
| small_battery | 20 | E_fixed_portfolio | 11/12 | 0.917 | 444.757 | 441.094 | 404.700 | 0.011441 | 11.43 |
| small_battery | 20 | E_adaptive_portfolio | 11/12 | 0.917 | 437.523 | 441.094 | 396.929 | 0.013256 | 12.62 |
| small_battery | 50 | B_nearest_customer | 12/12 | 1.000 | 790.149 | 772.299 | 708.877 | 0.001422 | 0.00 |
| small_battery | 50 | D_composite_inter_route | 12/12 | 1.000 | 727.451 | 729.939 | 594.360 | 0.095130 | 0.00 |
| small_battery | 50 | E_fixed_portfolio | 12/12 | 1.000 | 677.475 | 669.304 | 594.360 | 0.186841 | 15.18 |
| small_battery | 50 | E_adaptive_portfolio | 12/12 | 1.000 | 679.924 | 666.961 | 624.259 | 0.162659 | 13.96 |
| small_battery | 100 | B_nearest_customer | 12/12 | 1.000 | 1165.372 | 1168.291 | 1078.626 | 0.006782 | 0.00 |
| small_battery | 100 | D_composite_inter_route | 12/12 | 1.000 | 1039.945 | 1033.596 | 940.793 | 0.740414 | 0.00 |
| small_battery | 100 | E_fixed_portfolio | 12/12 | 1.000 | 990.187 | 991.639 | 908.911 | 1.619952 | 15.93 |
| small_battery | 100 | E_adaptive_portfolio | 12/12 | 1.000 | 994.978 | 1006.292 | 902.816 | 0.996815 | 15.43 |

## Portfolio comparisons

Negative objective percentage means the tested method is shorter.

| Profile | n | Tested | Reference | Feasibility delta | Objective delta (%) | Runtime delta (s) | W/T/L |
|---|---:|---|---|---:|---:|---:|---:|
| baseline | 20 | E_fixed_portfolio | B_nearest_customer | 0.000 | -14.78 | 0.011778 | 12/0/0 |
| baseline | 20 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -3.51 | 0.005792 | 3/9/0 |
| baseline | 20 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -15.08 | 0.015224 | 12/0/0 |
| baseline | 20 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -3.85 | 0.009239 | 6/6/0 |
| baseline | 50 | E_fixed_portfolio | B_nearest_customer | 0.000 | -11.47 | 0.210552 | 12/0/0 |
| baseline | 50 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -7.65 | 0.096065 | 8/4/0 |
| baseline | 50 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -11.12 | 0.188625 | 12/0/0 |
| baseline | 50 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -7.29 | 0.074138 | 10/0/2 |
| baseline | 100 | E_fixed_portfolio | B_nearest_customer | 0.000 | -16.42 | 1.796584 | 12/0/0 |
| baseline | 100 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -6.28 | 0.879896 | 9/3/0 |
| baseline | 100 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -16.18 | 1.205173 | 12/0/0 |
| baseline | 100 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -6.01 | 0.288486 | 10/0/2 |
| small_battery | 20 | E_fixed_portfolio | B_nearest_customer | 0.083 | -9.59 | 0.011169 | 10/0/0 |
| small_battery | 20 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -5.03 | 0.004639 | 7/4/0 |
| small_battery | 20 | E_adaptive_portfolio | B_nearest_customer | 0.083 | -11.06 | 0.012985 | 10/0/0 |
| small_battery | 20 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -6.57 | 0.006454 | 10/1/0 |
| small_battery | 50 | E_fixed_portfolio | B_nearest_customer | 0.000 | -14.26 | 0.185420 | 12/0/0 |
| small_battery | 50 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -6.87 | 0.091712 | 10/2/0 |
| small_battery | 50 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -13.95 | 0.161237 | 12/0/0 |
| small_battery | 50 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -6.53 | 0.067529 | 11/0/1 |
| small_battery | 100 | E_fixed_portfolio | B_nearest_customer | 0.000 | -15.03 | 1.613169 | 12/0/0 |
| small_battery | 100 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -4.78 | 0.879538 | 9/3/0 |
| small_battery | 100 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -14.62 | 0.990032 | 12/0/0 |
| small_battery | 100 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -4.32 | 0.256401 | 10/1/1 |
| tight_tw | 20 | E_fixed_portfolio | B_nearest_customer | 0.000 | -14.92 | 0.011799 | 12/0/0 |
| tight_tw | 20 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -2.92 | 0.005417 | 5/7/0 |
| tight_tw | 20 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -15.25 | 0.015325 | 12/0/0 |
| tight_tw | 20 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -3.30 | 0.008943 | 7/5/0 |
| tight_tw | 50 | E_fixed_portfolio | B_nearest_customer | 0.000 | -12.23 | 0.199855 | 12/0/0 |
| tight_tw | 50 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -4.17 | 0.083729 | 6/6/0 |
| tight_tw | 50 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -12.52 | 0.186461 | 12/0/0 |
| tight_tw | 50 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -4.49 | 0.070335 | 8/2/2 |
| tight_tw | 100 | E_fixed_portfolio | B_nearest_customer | 0.000 | -16.34 | 1.865292 | 12/0/0 |
| tight_tw | 100 | E_fixed_portfolio | D_composite_inter_route | 0.000 | -6.10 | 0.924483 | 11/1/0 |
| tight_tw | 100 | E_adaptive_portfolio | B_nearest_customer | 0.000 | -15.59 | 1.183959 | 12/0/0 |
| tight_tw | 100 | E_adaptive_portfolio | D_composite_inter_route | 0.000 | -5.27 | 0.243150 | 11/0/1 |

## Diagnostics

- `small_battery` n=20 seed=20280818 method=B_nearest_customer: feasible=False, runtime=0.000294s, termination=reference_method, violations=['unserved customers: [8]']
- `small_battery` n=20 seed=20280822 method=B_nearest_customer: feasible=False, runtime=0.000279s, termination=reference_method, violations=['unserved customers: [18]']
- `small_battery` n=20 seed=20280822 method=D_composite_inter_route: feasible=False, runtime=0.005832s, termination=reference_method, violations=['unserved customers: [6]']
- `small_battery` n=20 seed=20280822 method=E_fixed_portfolio: feasible=False, runtime=0.000611s, termination=infeasible_construction, violations=['unserved customers: [6]']
- `small_battery` n=20 seed=20280822 method=E_adaptive_portfolio: feasible=False, runtime=0.000605s, termination=infeasible_construction, violations=['unserved customers: [6]']
- `tight_tw` n=100 seed=20360819 method=E_adaptive_portfolio: feasible=True, runtime=1.276020s, termination=budget, violations=[]
- `baseline` n=100 seed=20360822 method=E_adaptive_portfolio: feasible=True, runtime=1.268678s, termination=budget, violations=[]
- `baseline` n=100 seed=20360814 method=E_adaptive_portfolio: feasible=True, runtime=1.262950s, termination=budget, violations=[]
- `baseline` n=100 seed=20360818 method=E_adaptive_portfolio: feasible=True, runtime=1.244167s, termination=budget, violations=[]
