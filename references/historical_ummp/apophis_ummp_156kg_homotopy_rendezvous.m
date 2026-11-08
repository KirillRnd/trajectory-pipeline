function apophis_ummp_156kg_homotopy_rendezvous
% Feasibility-first PMP shooting with continuation to exact bang-bang.

clc;
param = struct();
ae = []; mug_0 = []; T_earth = []; r_unit = []; V_unit = []; T_unit = []; a_unit = []; %#ok<NASGU>
standart_parameters
param.m0 = 156;
param.type_of_problem = "встреча";
param.target_body = "ApophisNew";
param.for_r_soi = 0;

seed = load('apophis_ummp_best_pmp_seed.mat');
old = load('apophis_ummp_bangbang_fmincon_full_costates_tof_algorithms_wide_from_active.mat');

X_center = old.best_XF(:);
X_scale = [
    max(abs(X_center(1:3)), 0.08*ones(3,1));
    max(abs(X_center(4:6)), 1e-7*ones(3,1));
    100;
    70
];
Z = zeros(8,1);
lb = -5*ones(8,1);
ub =  5*ones(8,1);
lb(8) = max(lb(8), (240-X_center(8))/X_scale(8));
ub(8) = min(ub(8), (580-X_center(8))/X_scale(8));

% The continuation step is adapted automatically.  Failed trial stages are
% rejected and retried from the last feasible branch point with half-step.
ode_rtol = 1e-12;
ode_atol = 1e-14;
anchor_weight = 1e-10;

history = cell(0,1);
best_feasible = [];
current_width = 202;
width_step = 2;
previous_width = NaN;
previous_Z = [];

% Resume from the sharpest already converged branch point when available.
resume_file = 'apophis_ummp_156kg_homotopy_rendezvous.mat';
checkpoint_file = 'apophis_ummp_156kg_homotopy_checkpoint.mat';
if isfile(checkpoint_file)
    resume_file = checkpoint_file;
end
if isfile(resume_file)
    resume = load(resume_file);
    if isfield(resume, 'best_feasible') && ~isempty(resume.best_feasible)
        best_feasible = resume.best_feasible;
        Z = best_feasible.Z;
        if isfield(resume, 'history'); history = resume.history; end
        current_width = best_feasible.switch_width;
        if isfield(resume, 'width_step'); width_step = resume.width_step; end
        accepted_rows = {};
        for ih = 1:numel(history)
            hh = history{ih};
            if hh.result.ok && norm(hh.result.ceq,inf) < 3e-7 && hh.result.m_used_kg < 64
                accepted_rows{end+1,1} = hh; %#ok<AGROW>
            end
        end
        if numel(accepted_rows) >= 2
            previous_width = accepted_rows{end-1}.switch_width;
            previous_Z = accepted_rows{end-1}.Z;
        end
        fprintf('Resuming from switch width %.6g\n', best_feasible.switch_width);
    end
end

stage = 0;
max_stages = 250;
while current_width > 0 && stage < max_stages
    stage = stage + 1;
    if current_width < 0.02
        width = 0;
    else
        width = max(0, current_width-width_step);
    end
    fprintf('\n============================================================\n');
    fprintf('Homotopy trial %d, switch width %.9g -> %.9g (step %.6g)\n', ...
        stage, current_width, width, current_width-width);
    fprintf('============================================================\n');

    cache_z = [];
    cache_result = [];
    Z_base = Z;
    if ~isempty(previous_Z) && current_width ~= previous_width
        tangent = (Z-previous_Z)/(current_width-previous_width);
        Z_predict = Z + tangent*(width-current_width);
        Z_predict = min(max(Z_predict,lb),ub);
    else
        Z_predict = Z;
    end
    Z_anchor = Z_predict;

    options = optimoptions('lsqnonlin', ...
        'Algorithm', 'trust-region-reflective', ...
        'Display', 'iter', ...
        'MaxIterations', 300, ...
        'MaxFunctionEvaluations', 20000, ...
        'FunctionTolerance', 1e-16, ...
        'StepTolerance', 1e-14, ...
        'OptimalityTolerance', 1e-13, ...
        'FiniteDifferenceType', 'central', ...
        'FiniteDifferenceStepSize', 3e-5, ...
        'OutputFcn', @save_iteration);

    [Z_new, resnorm, residual, exitflag, output] = lsqnonlin( ...
        @shooting_residual, Z_predict, lb, ub, options);
    result = evaluate(Z_new);

    row = struct('stage', stage, 'switch_width', width, 'Z', Z_new, ...
        'X', X_center + X_scale.*Z_new, 'resnorm', resnorm, ...
        'residual', residual, 'exitflag', exitflag, 'output', output, ...
        'result', result);
    history{end+1,1} = row; %#ok<AGROW>

    fprintf('Stage result: r=%.12g km, v=%.12g m/s, fuel=%.12g kg, coast=%.12g d\n', ...
        result.r_res_km, result.v_res_m_s, result.m_used_kg, result.final_coast_days);

    accepted = result.ok && norm(result.ceq, inf) < 3e-7 ...
        && result.m_used_kg < 64;
    if accepted
        previous_Z = Z_base;
        previous_width = current_width;
        Z = Z_new;
        current_width = width;
        best_feasible = row;
        width_step = min(1.35*width_step, max(1e-4,0.12*max(current_width,1e-3)));
        fprintf('Accepted. Next continuation step %.6g\n', width_step);
    else
        width_step = width_step/2;
        fprintf('Rejected. Retrying from width %.9g with step %.6g\n', ...
            current_width, width_step);
        if width_step < 1e-5*max(1,current_width)
            warning('Adaptive continuation step became too small.');
            break
        end
    end

    save('apophis_ummp_156kg_homotopy_checkpoint.mat', ...
        'history', 'Z', 'X_center', 'X_scale', 'lb', 'ub', ...
        'current_width', 'width_step', 'ode_rtol', 'ode_atol', ...
        'anchor_weight', 'best_feasible', 'previous_width', 'previous_Z');
end

if isempty(best_feasible)
    save('apophis_ummp_156kg_homotopy_failed.mat', ...
        'history', 'Z', 'X_center', 'X_scale', 'current_width');
    error('No feasible rendezvous below 64 kg was obtained.');
end

result = best_feasible.result;
XF = best_feasible.X;
save('apophis_ummp_156kg_homotopy_rendezvous.mat', ...
    'result', 'XF', 'best_feasible', 'history', 'X_center', 'X_scale');
plot_solution(result, param, best_feasible.switch_width);
savefig(gcf, 'apophis_ummp_156kg_homotopy_rendezvous.fig');
exportgraphics(gcf, 'apophis_ummp_156kg_homotopy_rendezvous.png', 'Resolution', 220);

fprintf('\nBEST FEASIBLE SOLUTION\n');
fprintf('switch width       = %.12g\n', best_feasible.switch_width);
fprintf('tof                = %.12g days\n', XF(8));
fprintf('fuel               = %.12g kg\n', result.m_used_kg);
fprintf('position residual  = %.12g km\n', result.r_res_km);
fprintf('velocity residual  = %.12g m/s\n', result.v_res_m_s);
fprintf('final coast        = %.12g days\n', result.final_coast_days);

    function residual_out = shooting_residual(Z_eval)
        R = evaluate(Z_eval);
        if ~R.ok
            residual_out = 1e3*ones(8,1);
            return
        end
        residual_out = [R.ceq; anchor_weight*(Z_eval(7:8)-Z_anchor(7:8))];
    end

    function R = evaluate(Z_eval)
        Z_eval = Z_eval(:);
        if ~isempty(cache_z) && isequal(Z_eval, cache_z)
            R = cache_result;
            return
        end
        X = X_center + X_scale.*Z_eval;
        R = propagate(X, width);
        cache_z = Z_eval;
        cache_result = R;
    end

    function stop = save_iteration(Z_eval, optimValues, state)
        stop = false;
        if strcmp(state, 'iter') && mod(optimValues.iteration, 10) == 0
            R = evaluate(Z_eval);
            fprintf('  physical: r=%g km, v=%g m/s, fuel=%g kg, tof=%g d\n', ...
                R.r_res_km, R.v_res_m_s, R.m_used_kg, R.tof_days);
            checkpoint = struct('stage', stage, 'width', width, ...
                'Z', Z_eval, 'result', R, 'optimValues', optimValues);
            save('apophis_ummp_156kg_homotopy_iteration.mat', 'checkpoint');
        end
    end

    function R = propagate(X, width_local)
        R = empty_result();
        R.X = X;
        R.tof_days = X(8);
        if X(8) < 230 || X(8) > 590
            return
        end

        st.t = seed.launch_jd + X(8);
        st.planet = 'ApophisNew';
        st.mode = 'Simple';
        [rt, vt] = planetModel(st);
        rt = rt'*1e3;
        vt = vt'*1e3;
        Y0 = [seed.r0_m; seed.v0_m_s; 0; X(4:6); X(1:3); X(7)];
        tf = X(8)*86400;
        ode_options = odeset('RelTol', ode_rtol, 'AbsTol', ode_atol, ...
            'Events', @(t,y) eventIntegrationTrajStopM(t,y,param));
        try
            ws = warning('off', 'MATLAB:ode15s:IntegrationTolNotMet');
            wc = onCleanup(@() warning(ws));
            [ts, Ys] = ode15s(@(t,y) integrate_dmdt_optimal_regularized( ...
                t,y,param,width_local), [0 tf], Y0, ode_options);
            clear wc
        catch
            return
        end
        if isempty(ts) || ts(end) < tf-1e-6
            return
        end

        dr = Ys(end,1:3)'-rt;
        dv = Ys(end,4:6)'-vt;
        ceq = [dr/param.r_unit; dv/param.V_unit];
        thrust = zeros(size(ts));
        switch_values = zeros(size(ts));
        for kk = 1:numel(ts)
            [thrust(kk), switch_values(kk)] = reconstructed_thrust(ts(kk),Ys(kk,:)',width_local);
        end
        active = thrust > 0.01*max(thrust);
        last_active = find(active,1,'last');
        if isempty(last_active)
            coast = X(8);
        else
            coast = (ts(end)-ts(last_active))/86400;
        end

        R.ok = true;
        R.ceq = ceq;
        R.r_res_km = norm(dr)/1e3;
        R.v_res_m_s = norm(dv);
        R.m_used_kg = Ys(end,7);
        R.final_coast_days = coast;
        R.t_sol = ts;
        R.Y_sol = Ys;
        R.thrust_N = thrust;
        R.switch_values = switch_values;
        R.target_r_f = rt;
        R.target_v_f = vt;
    end

    function [F, Sval] = reconstructed_thrust(t,y,width_local)
        r = y(1:3);
        mass = param.m0-y(7);
        pv = y(11:13);
        pm = y(14);
        u = u_from_rt(t,r,param);
        gm = gamma_max_from_rt(t,r,param);
        Sval = param.m_compensation*(1+pm)-(u/mass)*norm(pv);
        if width_local > 0
            gamma = gm*0.5*(1-tanh(Sval/width_local));
        elseif Sval < -1e-8
            gamma = gm;
        else
            gamma = 0;
        end
        F = gamma*u;
    end
end

function R = empty_result
R = struct('ok',false,'X',NaN(8,1),'tof_days',NaN, ...
    'ceq',1e3*ones(6,1),'r_res_km',inf,'v_res_m_s',inf, ...
    'm_used_kg',inf,'final_coast_days',inf,'t_sol',[],'Y_sol',[], ...
    'thrust_N',[],'switch_values',[],'target_r_f',[],'target_v_f',[]);
end

function plot_solution(R,param,width)
figure('Color','w','Position',[100 100 1450 650]);
tiledlayout(1,2,'Padding','compact','TileSpacing','compact');
nexttile;
plot3(R.Y_sol(:,1)/param.r_unit,R.Y_sol(:,2)/param.r_unit, ...
    R.Y_sol(:,3)/param.r_unit,'k-','LineWidth',1.8);
hold on;
plot3(R.target_r_f(1)/param.r_unit,R.target_r_f(2)/param.r_unit, ...
    R.target_r_f(3)/param.r_unit,'mo','MarkerFaceColor','m');
plot3(R.Y_sol(end,1)/param.r_unit,R.Y_sol(end,2)/param.r_unit, ...
    R.Y_sol(end,3)/param.r_unit,'ko','MarkerFaceColor','k');
axis equal; grid on; view(2);
xlabel('x, а.е.'); ylabel('y, а.е.'); title('Траектория встречи');
legend('УММП','Апофис','Конечная точка УММП','Location','best');
nexttile;
plot(R.t_sol/86400,R.thrust_N*1e3,'k-','LineWidth',1.6);
grid on; xlabel('Время, сут'); ylabel('Тяга, мН');
title(sprintf('Профиль тяги, ширина переключения %.3g',width));
end
