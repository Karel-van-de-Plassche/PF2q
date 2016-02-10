
theta = linspace(0,2*pi,100);
for i = 1:length(theta)
    sum_result(i) = 0;
    for j = 2:length(boundary)
        sum_result(i) = sum_result(i) + complex(boundary(j,1),boundary(j,2)) * exp(complex(0,j-1)*theta(i));
    end
end
     %sum_result(i) = np.sum([np.complex(row[0], row[1]) * np.exp(np.complex(0,m*dtheta)) for m, row in enumerate(boundary[1:,:])])
a_0=0.513;
r = a_0 * (boundary(1,1)/2 + real(sum_result));
%R0 = 2
X = r .* cos(theta)
Z = -r .* sin(theta)

plot(X,Z)
xlim([-1.5,1.5])
ylim([-1.5,1.5])