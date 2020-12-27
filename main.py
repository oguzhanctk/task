import helpers

@helpers.timer
def main(limit=40, count=48, tpv=10000):
     '''
     
     Parameters
     ----------
     limit : int, optional
          The default is 40 because of more 
          stocks taking huge time to calculate.
     count : int, optional
          How many records are getting from 
          database(default period is 60). The default is 48.
     tpv : int, optional
          Total portfolio value. The default is 10000.

     Returns
     -------
     alloc : dict, allocation for TPV.

     '''
     alloc, lo = helpers.calculateInvestment(limit=limit,
                                             count=count, 
                                             tpv=tpv,
                                             show_cla=False,
                                             write_to_file=True)
     return alloc


if __name__ == "__main__":
     
     res = main()
     print(res)