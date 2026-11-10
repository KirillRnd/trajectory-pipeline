% fmincon optimization in full initial costates + time of flight.
%
% Variables in physical problem:
%   X_full(1:3) = pv0, MATLAB scale
%   X_full(4:6) = pr0, MATLAB scale
%   X_full(7)   = pm0
%   X_full(8)   = tof_days
%
% Numerically fmincon sees normalized Z:
%   X_full = X_center + X_scale .* Z
%
% Start point is the result of
% apophis_ummp_bangbang_fmincon_full_costates_scaled.m.

clc;
clear;

standart_parameters
seed = load('apophis_ummp_best_pmp_seed.mat');

param.type_of_problem = "РІСЃС‚СЂРµС‡Р°";
param.target_body = "ApophisNew";
param.t_start = seed.launch_jd;
param.target_time_uses_delta_start = true;
param.for_r_soi = 0;

ctx = struct();
ctx.seed = seed;
ctx.param = param;
ctx.launch_jd = seed.launch_jd;

% Previous full-costate result.
pv0_center = [
   -0.408948598532213
    0.2134411025007301
   -0.1137204008875895
];

pr0_center = [
    8.299359596429851e-08
   -1.570630365860462e-07
    3.037130623139088e-07
];

pm0_center = 192.7038621928454;
tof_days_center = seed.tof_days;

X_center = [pv0_center; pr0_center; pm0_center; tof_days_center];

% Component scales for normalized optimization.
X_scale = [
    max(abs(pv0_center), 0.08 * ones(3,1));
    max(abs(pr0_center), 0.8e-7 * ones(3,1));
    60;
    35
];

ctx.X_center = X_center;
ctx.X_scale = X_scale;

Z0 = zeros(8,1);

% Moderate box around current branch.
lb = -ones(8,1);
ub =  ones(8,1);
lb(7) = -1.5;  % pm0
ub(7) =  1.5;
lb(8) = -1.5;  % tof_days
ub(8) =  1.5;

objective = @(Z) local_objective_scaled(Z, ctx);

options = optimoptions('fmincon', 'Algorithm', 'sqp');
options = optimoptions(options, 'Display', 'iter');
options = optimoptions(options, 'MaxIterations', 140);
options = optimoptions(options, 'MaxFunctionEvaluations', 3200);
options = optimoptions(options, 'OptimalityTolerance', 1e-8);
options = optimoptions(options, 'StepTolerance', 1e-8);
options = optimoptions(options, 'ConstraintTolerance', 1e-8);
options = optimoptions(options, 'FiniteDifferenceType', 'central');
options = optimoptions(options, 'FiniteDifferenceStepSize', 1e-3);
options = optimoptions(options, 'ScaleProblem', false);
options = optimoptions(options, 'OutputFcn', @(Z, optimValues, state) local_output(Z, optimValues, state, ctx));

fprintf('Apophis bang-bang fmincon: full costates + TOF\n');
fprintf('X_center pm0 = %.16g, tof = %.9g days\n', pm0_center, tof_days_center);
fprintf('X_center |pv0| = %.16g, |pr0| = %.16g\n', norm(pv0_center), norm(pr0_center));
fprintf('X_scale  = ['); fprintf(' %.6g', X_scale); fprintf(' ]\n');

[ZF, JF, exitflag, output] = fmincon(objective, Z0, [], [], [], [], lb, ub, [], options);

XF = X_center + X_scale .* ZF;
[JF_check, result] = local_objective_full(XF, ctx);

fprintf('\nFinal full-costates + TOF result\n');
fprintf('exitflag = %d\n', exitflag);
disp(output);
fprintf('ZF = ['); fprintf(' %.9g', ZF); fprintf(' ]\n');
fprintf('J = %.16g, J_check = %.16g\n', JF, JF_check);
fprintf('pv0 = [%.16g %.16g %.16g]\n', XF(1), XF(2), XF(3));
fprintf('pr0 = [%.16g %.16g %.16g]\n', XF(4), XF(5), XF(6));
fprintf('pm0 = %.16g\n', XF(7));
fprintf('tof_days = %.16g\n', XF(8));
fprintf('arrival JD = %.16g\n', result.arrival_jd);
fprintf('r residual = %.9g km\n', result.r_res_km);
fprintf('v residual = %.9g m/s\n', result.v_res_m_s);
fprintf('fuel used  = %.9g kg\n', result.m_used_kg);
fprintf('active     = %.9g days\n', result.active_days);
fprintf('switches   = %d\n', result.switch_count);

save('apophis_ummp_bangbang_fmincon_full_costates_tof.mat', ...
    'ZF', 'XF', 'JF', 'exitflag', 'output', 'result', 'X_center', 'X_scale', 'lb', 'ub');

local_plot_result(result, ctx, XF);
saveas(gcf, 'apophis_ummp_bangbang_fmincon_full_costates_tof.png');
savefig(gcf, 'apophis_ummp_bangbang_fmincon_full_costates_tof.fig');

function [J, result] = local_objective_scaled(Z, ctx)
    X = ctx.X_center + ctx.X_scale .* Z(:);
    [J, result] = local_objective_full(X, ctx);
end

function [J, result] = local_objective_full(X, ctx)
    seed = ctx.seed;
    param = ctx.param;

    pv0 = X(1:3);
    pr0 = X(4:6);
    pm0 = X(7);
    tof_days = X(8);
    tof_seconds = tof_days * 86400;
    arrival_jd = ctx.launch_jd + tof_days;

    result = struct();
    result.X = X(:);
    result.ok = false;
    result.arrival_jd = arrival_jd;
    result.r_res_km = inf;
    result.v_res_m_s = inf;
    result.m_used_kg = inf;
    result.active_days = inf;
    result.switch_count = inf;
    result.message = "";
    result.t_sol = [];
    result.Y_sol = [];
    result.thrust_N = [];
    result.target_r_f = [];
    result.target_v_f = [];
    result.score = inf;

    try
        if tof_days < 250 || tof_days > 520
            J = 1e12 + (tof_days - 390)^2;
            result.message = "tof outside guard";
            return
        end

        st.t = arrival_jd;
        st.planet = 'ApophisNew';
        st.mode = 'Simple';
        [target_r_f, target_v_f] = planetModel(st);
        target_r_f = target_r_f' * 1e3;
        target_v_f = target_v_f' * 1e3;

        Y0 = [seed.r0_m; seed.v0_m_s; 0; pr0; pv0; pm0];

        options_ode = odeset('RelTol', 1e-12, 'AbsTol', 1e-14);
        options_ode = odeset(options_ode, 'Events', @(s, y) eventIntegrationTrajStopM(s, y, param));
        [t_sol, Y_sol] = ode15s(@(t, Y) integrate_dmdt_optimal(t, Y, param), [0, tof_seconds], Y0, options_ode);

        SC_rf = Y_sol(end, 1:3)';
        SC_vf = Y_sol(end, 4:6)';
        r_vec = (SC_rf - target_r_f) / param.r_unit;
        v_vec = (SC_vf - target_v_f) / param.V_unit;

        r_res_km = norm(SC_rf - target_r_f) / 1000;
        v_res_m_s = norm(SC_vf - target_v_f);

        thrust_N = zeros(size(t_sol));
        for k = 1:numel(t_sol)
            thrust_N(k) = evaluate_ummp_thrust_force(t_sol(k), Y_sol(k,:)', param);
        end
        active = thrust_N > 1e-9;
        active_days = trapz(t_sol, double(active)) / 86400;
        switch_count = sum(abs(diff(active)) > 0);

        residual = [r_vec; v_vec];
        J = residual' * residual;

        if Y_sol(end,7) > 90
            J = J + 1e-3 * ((Y_sol(end,7) - 90) / 10)^2;
        end

        result.ok = true;
        result.arrival_jd = arrival_jd;
        result.r_res_km = r_res_km;
        result.v_res_m_s = v_res_m_s;
        result.m_used_kg = Y_sol(end,7);
        result.active_days = active_days;
        result.switch_count = switch_count;
        result.t_sol = t_sol;
        result.Y_sol = Y_sol;
        result.thrust_N = thrust_N;
        result.target_r_f = target_r_f;
        result.target_v_f = target_v_f;
        result.score = J;
        result.message = "ok";

    catch ME
        J = 1e20;
        result.message = string(ME.message);
    end
end

function stop = local_output(Z, optimValues, state, ctx)
    stop = false;
    if strcmp(state, 'iter')
        X = ctx.X_center + ctx.X_scale .* Z(:);
        fprintf('  iter: J=% .9g pm0=% .9g tof=% .6f |pv0|=% .9g |pr0|=% .9g Znorm=% .4g\n', ...
            optimValues.fval, X(7), X(8), norm(X(1:3)), norm(X(4:6)), norm(Z));
    end
end

function local_plot_result(result, ctx, XF)
    figure(4601); clf;
    tiledlayout(2,2);

    nexttile;
    plot3(result.Y_sol(:,1) / ctx.param.r_unit, result.Y_sol(:,2) / ctx.param.r_unit, result.Y_sol(:,3) / ctx.param.r_unit, ...
        'm', 'LineWidth', 1.5);
    hold on;
    plot3(result.target_r_f(1) / ctx.param.r_unit, result.target_r_f(2) / ctx.param.r_unit, result.target_r_f(3) / ctx.param.r_unit, ...
        'ro', 'MarkerFaceColor', 'r', 'DisplayName', 'Target');
    plot3(result.Y_sol(end,1) / ctx.param.r_unit, result.Y_sol(end,2) / ctx.param.r_unit, result.Y_sol(end,3) / ctx.param.r_unit, ...
        'go', 'MarkerFaceColor', 'g', 'DisplayName', 'SC final');
    grid on; axis equal; view(0,90);
    xlabel('X, a.e.'); ylabel('Y, a.e.');
    title('Trajectory');
    legend('Location', 'best');

    nexttile;
    stairs(result.t_sol / 86400, result.thrust_N * 1000, 'LineWidth', 1.2);
    grid on;
    xlabel('t, days'); ylabel('Thrust, mN');
    title('Bang-bang thrust');

    nexttile;
    plot(result.t_sol / 86400, result.Y_sol(:,7), 'LineWidth', 1.2);
    grid on;
    xlabel('t, days'); ylabel('mUsed, kg');
    title('Fuel');

    nexttile;
    text(0.05, 0.88, sprintf('tof = %.9g days', XF(8)));
    text(0.05, 0.76, sprintf('pm0 = %.9g', XF(7)));
    text(0.05, 0.64, sprintf('|pv0| = %.9g', norm(XF(1:3))));
    text(0.05, 0.52, sprintf('|pr0| = %.9g', norm(XF(4:6))));
    text(0.05, 0.38, sprintf('r = %.6g km', result.r_res_km));
    text(0.05, 0.26, sprintf('v = %.6g m/s', result.v_res_m_s));
    text(0.05, 0.14, sprintf('fuel = %.6g kg', result.m_used_kg));
    axis off;
    title('Summary');

    sgtitle(sprintf('Full costates + TOF: J=%.6g, switches=%d', result.score, result.switch_count));
end


