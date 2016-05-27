import math
import numpy

ASY_SAFEGUARD = 1.0002
EXP_SAFEGUARD = 709.78
H2O_K1 = +1.5587e+0
H2O_K2 = +6.9390e-2
H2O_K3 = -2.7816e-4
H2O_K4 = +6.8455e-7
TAO_TATM_MIN = -30.0	
TAO_TATM_MAX  = 90.0
TAO_SQRTH2OMAX = 6.2365
TAO_COMP_MIN = 0.400
TAO_COMP_MAX = 1.000

class RadiometricData:

	
	lPixval = None # the radiometric data
	Tkelvin = None # the output temperature data
	
	m_RelHum = 0.5
	m_AtmTemp = 293.15
	m_ObjectDistance = 1
	m_X = 1.9
	m_alpha1 = 0.006569
	m_beta1 = -0.002276
	m_beta2 = -0.00667
	m_alpha2 = 0.01262
	m_AtmTao = None
	m_Emissivity = 0.95
	m_ExtOptTransm = 1
	m_K1 = None
	m_K2 = None
	m_ExtOptTemp = 293.15
	m_AmbTemp = 293.15
	m_J0 = 4214
	m_J1 = 69.6245
	m_R = 16671.9043
	m_F = 1
	m_B = 1430.1
	

	def __init__(self):
		pass

	def doCalcAtmTao(self):
		#double tao, dtao
		#double H, T, sqrtD, X, a1, b1, a2, b2
		#double sqrtH2O
		#double TT
		#double a1b1sqH2O, a2b2sqH2O, exp1, exp2
	
		H = self.m_RelHum
		C = self.m_AtmTemp
		T = (C - 273.15)
		#print("t atm = %.2f" % T)
		#T = C.Value() # We need Celsius to use constants defined above
		sqrtD = math.sqrt(self.m_ObjectDistance)
		X  = self.m_X
		a1 = self.m_alpha1	  
		b1 = self.m_beta1
		a2 = self.m_alpha2
		b2 = self.m_beta2 
	
		if (T < TAO_TATM_MIN):
			T = TAO_TATM_MIN
		elif (T > TAO_TATM_MAX):
			T = TAO_TATM_MAX
	   
		TT = T*T
	
		sqrtH2O = math.sqrt(H*math.exp(H2O_K1 + H2O_K2*T + H2O_K3*TT + H2O_K4*TT*T))
	
		if (sqrtH2O > TAO_SQRTH2OMAX):
			sqrtH2O = TAO_SQRTH2OMAX
	   
		a1b1sqH2O = (a1+b1*sqrtH2O)
		a2b2sqH2O = (a2+b2*sqrtH2O)
		exp1 = math.exp(-sqrtD*a1b1sqH2O)
		exp2 = math.exp(-sqrtD*a2b2sqH2O) 
	
		tao = X*exp1 + (1-X)*exp2
		dtao = -(a1b1sqH2O*X*exp1+a2b2sqH2O*(1-X)*exp2) 
		# The real D-derivative is also divided by 2 and sqrtD.
		# Here we only want the sign of the slope!

		if (tao < TAO_COMP_MIN):
			tao = TAO_COMP_MIN		# below min value, clip

		elif (tao > TAO_COMP_MAX):
			# check tao at 1 000 000 m dist
			tao = X*math.exp(-(1.0E3)*a1b1sqH2O)+(1.0-X)*math.exp(-(1.0E3)*a2b2sqH2O)

			# above max, staying up, assume \/-shape
			if (tao > 1.0):
				tao = TAO_COMP_MIN
			else:
				tao = TAO_COMP_MAX # above max, going down, assume /\-shape

		elif ( dtao > 0.0 and self.m_ObjectDistance > 0.0):
			tao = TAO_COMP_MIN	 # beween max & min, going up, assume \/

		# else between max & min, going down => OK as it is, -)

		return( tao)


	def doCalcK1(self):
		#dblVal = 1.0

		dblVal = self.m_AtmTao * self.m_Emissivity * self.m_ExtOptTransm

		if (dblVal > 0.0):
			dblVal = 1/dblVal

		return (dblVal)


	def doCalcK2(self, dAmbObjSig, dAtmObjSig, dExtOptTempObjSig):
		#double emi
		temp1 = 0.0
		temp2 = 0.0
		temp3 = 0.0
	
		emi = self.m_Emissivity

		if (emi > 0.0):
			temp1 = (1.0 - emi)/emi * dAmbObjSig

			if (self.m_AtmTao > 0.0):
				temp2 = (1.0 - self.m_AtmTao)/(emi*self.m_AtmTao)* dAtmObjSig

			if (self.m_ExtOptTransm > 0.0 and self.m_ExtOptTransm < 1.0):
				temp3 = (1.0 - self.m_ExtOptTransm) / (emi*self.m_AtmTao*self.m_ExtOptTransm)* dExtOptTempObjSig
	
		return (temp1 + temp2 + temp3)



	def tempToObjSig(self, dblKelvin):
		objSign = 0.0
		dbl_reg = dblKelvin

		# objSign = R / (exp(B/T) - F)
 
		if (dbl_reg > 0.0):
			dbl_reg = self.m_B / dbl_reg 

			if (dbl_reg < EXP_SAFEGUARD):
				dbl_reg = math.exp(dbl_reg) 
		 
				if (self.m_F <= 1.0):
					if ( dbl_reg < ASY_SAFEGUARD ):
						dbl_reg = ASY_SAFEGUARD # Don't get above a R/(1-F) (horizontal) asymptote
				else: 
					# F > 1.0
					if ( dbl_reg < self.m_F*ASY_SAFEGUARD ):
						dbl_reg = self.m_F*ASY_SAFEGUARD
						# Don't get too close to a B/ln(F) (vertical) asymptote
 
				objSign = self.m_R/(dbl_reg - self.m_F)
	
		return( objSign)



	def doUpdateCalcConst(self):
		self.m_AtmTao = self.doCalcAtmTao()

		self.m_K1 = self.doCalcK1()

		self.m_K2 = self.doCalcK2(self.tempToObjSig(self.m_AmbTemp),self.tempToObjSig(self.m_AtmTemp),self.tempToObjSig(self.m_ExtOptTemp))



	def imgToPow(self, lPixval):
		pow = (lPixval - self.m_J0) / self.m_J1
	
		return (pow)


	def powToObjSig(self, dPow):
		return (self.m_K1 * dPow - self.m_K2)


	def objSigToTemp(self, dObjSig):
		Tkelvin = 0.0

		# Tkelvin = B /log(R / objSign + F)
		#print(dObjSig)

		dbl_reg = self.m_R / dObjSig + self.m_F
	 
		if (self.m_F <= 1.0):
			if (dbl_reg < ASY_SAFEGUARD):
				dbl_reg = ASY_SAFEGUARD # Don't get above a R/(1-F) (horizontal) asymptote						
		else:
			tmp = self.m_F * ASY_SAFEGUARD
			if (dbl_reg < tmp):
				dbl_reg = tmp
				# Don't get too close to a B/ln(F) (vertical) asymptote
				
		Tkelvin = self.m_B / math.log(dbl_reg)	# changed from quicklog to log	 

		return (Tkelvin)
	
	

	def getTempFast(self):
		self.doUpdateCalcConst()

		dPow = (self.lPixval - self.m_J0) / self.m_J1
		dSig = self.m_K1 * dPow - self.m_K2
		dbl_reg = self.m_R / dSig + self.m_F

		if (self.m_F <= 1.0):
			dbl_reg[dbl_reg < ASY_SAFEGUARD] = ASY_SAFEGUARD
		else:
			tmp = m_F * ASY_SAFEGUARD
			dbl_reg[dbl_reg < tmp] = tmp
		
				
		self.Tkelvin = self.m_B / numpy.log(dbl_reg)
		return(self.Tkelvin)


d = RadiometricData()
d.lPixval = numpy.ones((640,480))*14000

#print(d.getTemp())
print(d.getTempFast())
d.lPixval = numpy.ones((640,480))*13000
print(d.getTempFast())
