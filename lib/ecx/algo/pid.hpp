#pragma once
#include <concepts>

namespace ecx::algo {

// Discrete PID controller with anti-windup output clamping.
// T must be a floating-point type (float or double).
template <std::floating_point T>
class Pid {
public:
    constexpr Pid(T kp, T ki, T kd, T output_limit)
        : kp_(kp), ki_(ki), kd_(kd), limit_(output_limit) {}

    // Compute one control step. dt is the time elapsed since the last call (seconds).
    T update(T setpoint, T feedback, T dt) {
        const T err = setpoint - feedback;
        integral_ += err * dt;
        const T derivative = (err - prev_err_) / dt;
        prev_err_          = err;

        T out = (kp_ * err) + (ki_ * integral_) + (kd_ * derivative);

        // 钳位输出，并在饱和方向继续吃误差时回退积分，防止 wind-up。
        const T sat = (out > limit_) ? T{1} : (out < -limit_ ? T{-1} : T{0});
        if (sat != T{0}) {
            out = sat * limit_;
            if (err * sat > T{0}) { integral_ -= err * dt; }
        }
        return out;
    }

    void reset() {
        integral_ = T{0};
        prev_err_ = T{0};
    }

    void set_gains(T kp, T ki, T kd) {
        kp_ = kp;
        ki_ = ki;
        kd_ = kd;
    }

private:
    T kp_, ki_, kd_, limit_;
    T integral_{};
    T prev_err_{};
};

}  // namespace ecx::algo
