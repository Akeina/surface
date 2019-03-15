# Function to calculate the Total Amps used. Takes in a float list of thruster PWMs
def get_amp_total(thruster_pwms):
    amp_total = 0

    for x in range(len(thruster_pwms)):
        amp_total += 214.9513 - 0.2864872 * thruster_pwms[x] + 0.00009537964 * (thruster_pwms[x] * thruster_pwms[x])
        # print(amp_total)
    return amp_total


# Function to readjust thruster PWM values if required. Takes in a float list of thruster PWMS,
# and  which is an int value representing a second amp limit (above the first) which once
# exceeded will also cause the top (first 4) thrusters to be scaled down.
def temp_safe_guard(thruster_pwms):
    amp_limit = 100

    if get_amp_total(thruster_pwms) <= amp_limit:
        return thruster_pwms
    else:
        while get_amp_total(thruster_pwms) > amp_limit:

            print(str(get_amp_total(thruster_pwms)) + " - " + str())

            for thrustNum in range(len(thruster_pwms)):
                if thruster_pwms[thrustNum] > 1500:
                    thruster_pwms[thrustNum] -= thruster_pwms[thrustNum] * 0.01
                elif thruster_pwms[thrustNum] < 1500:
                    thruster_pwms[thrustNum] += thruster_pwms[thrustNum] * 0.01

    thruster_pwms = [round(x) for x in thruster_pwms]
    return thruster_pwms


# Values will converge to 1500 (0 power) when adjusted
pwmList = [1900.0, 1100.0, 1700.0, 1700.0, 1700.0, 1700.0, 1700.0, 1700.0]
# print(get_amp_total(pwmList));
print(temp_safe_guard(pwmList))
